import os.path as osp

from flask import (Blueprint, current_app, flash, jsonify, redirect,
                   render_template, request, send_file, url_for)

from ..models import Annotation, Participant, Project
from ..utils.extensions import db
from ..utils.functions.annotator import (get_session_from_participant,
                                         save_annotations)
from ..utils.functions.common import get_current_time

participant = Blueprint('participant', __name__)

@participant.route('/join/<token>', methods=['GET'])
def join_session(token):
    """
    Allow a participant to join a session using a unique token.

    Parameters:
    - token (str): Unique token associated with the participant.

    Returns:
    - Response: Redirects to the annotator route or the core index based on the token validity.
    """
    current_app.logger.info(f"Attempting to join session with token: {token}")
    participant_instance = Participant.verify_token(token)
    if not participant_instance:
        current_app.logger.warning(f"Invalid or expired token: {token}")
        flash('The link is invalid or has expired.')
        return redirect(url_for('core.index'))

    session = get_session_from_participant(participant_instance)
    if not session:
        current_app.logger.warning(f"No session associated with token: {token}")
        flash('The session associated with this link is not available.')
        return redirect(url_for('core.index'))

    current_app.logger.info(f"Redirecting to annotator route with token: {token}")
    participant_instance.last_accessed = get_current_time()
    participant_instance.has_accessed = True
    db.session.commit()
    
    return redirect(url_for('participant.annotator', token=token))

@participant.route('/annotator/<token>', methods=['GET', 'POST'])
def annotator(token):
    """
    Annotator view where participants can annotate videos.

    Parameters:
    - token (str): Unique token associated with the participant.

    Returns:
    - Rendered Template: Displays the annotator interface.
    - JSON Response: Provides feedback on the annotation submission status.
    """
    participant_instance = Participant.verify_token(token)
    if not participant_instance:
        current_app.logger.warning(f"Invalid or expired token: {token}")
        return jsonify({"error": "Invalid or expired token"}), 400

    try: 
        session_instance = participant_instance.session
        if session_instance:
            project_instance = Project.query.get(session_instance.project_id)
        else:
            current_app.logger.warning(f"Session not found for participant with token: {token}")
            return jsonify({"error": "Session not found for this participant"}), 404

        if not project_instance:
            current_app.logger.warning(f"Project not found for participant with token: {token}")
            return jsonify({"error": "Project not found for this participant"}), 404

        if project_instance.settings:
            method = project_instance.settings.method
            bounding = project_instance.settings.bounding
            granularity = project_instance.settings.granularity
            slider_min = (granularity/2)*(-1)
            slider_max = (granularity/2)
            axis = project_instance.settings.axis
            ceiling = project_instance.settings.ceiling
            floor = project_instance.settings.floor
        else:
            current_app.logger.warning(f"Settings not found for project with ID: {project_instance.id}")
            return jsonify({"error": "Settings not found. Consult your researcher."}), 404

        if request.method == 'POST':
            current_app.logger.info(f"Received data: {request.json}")
            data = request.json
            if not data:
                current_app.logger.error(f"No JSON data received in the request.")
                return jsonify({"error": "No data received. Please ensure you're sending JSON data."}), 400

            annotations_data_map = data.get('annotations')
            
            for video_id_str, annotations_list in annotations_data_map.items():
                video_id = int(video_id_str)
                for annotation_data in annotations_list:
                    annotation = Annotation(
                        participant_id=participant_instance.id,
                        video_id=video_id,
                        timecode=annotation_data.get("timestamp"),
                        frame_number=annotation_data.get("video_frame"),
                        slider_position=annotation_data.get("slider_position"),
                        trigger=annotation_data.get("trigger")
                    )
                    db.session.add(annotation)

            try:
                save_annotations(request, participant_instance)
                current_app.logger.info(f"Annotations saved successfully for participant with token: {token}")
                return jsonify({"message": "Annotations submitted successfully! Thank you for your participation."}), 200
            except Exception as e:
                current_app.logger.error(f"Error saving annotations: {e}")
                return jsonify({"error": f"There was an error saving your annotations: {str(e)}"}), 500

        videos_data = []
        for video_assoc in participant_instance.video_associations:
            if project_instance.settings.coupling == "coupled" and video_assoc.owner:
                continue  # Skip this video if the participant is the owner in a coupled setting
            video_info = {
                "id": video_assoc.video.id,
                "url": url_for('participant.serve_video', project_id=project_instance.id, session_id=session_instance.id, filename=video_assoc.video.filename),
                "frame_rate": video_assoc.video.frame_rate
            }
            videos_data.append(video_info)

        current_app.logger.debug(f"videos_data: {videos_data}")

        return render_template('annotator.html', title='Annotator', participant=participant_instance, videos_data=videos_data, video_type="video/mp4", method=method, bounding=bounding, slider_min=slider_min, slider_max=slider_max, slider_value=0, axis=axis, ceiling=ceiling, floor=floor)

    except Exception as e:
        current_app.logger.error(f"Error in annotator route: {e}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

@participant.route('/uploads/<int:project_id>/<int:session_id>/<filename>')
def serve_video(project_id, session_id, filename):
    """
    Serve a video file for a given project and session.

    Parameters:
    - project_id (int): ID of the project.
    - session_id (int): ID of the session.
    - filename (str): Name of the video file to serve.

    Returns:
    - File Response: Sends the video file for download.
    - Response: Redirects to the core index in case of errors.
    """
    current_app.logger.info(f"Serving video with filename: {filename} for project ID: {project_id} and session ID: {session_id}")
    SESSION_FOLDER_PATH = osp.join(current_app.config.get('UPLOADS_FOLDER_PATH'), str(project_id), str(session_id))
    
    if not osp.exists(osp.join(SESSION_FOLDER_PATH, filename)):
        current_app.logger.error(f"File {filename} not found in directory {SESSION_FOLDER_PATH}")
        flash('Video file not found. Please contact the administrator.')
        return redirect(url_for('core.index'))
    
    current_app.logger.debug(f"UPLOADS_FOLDER_PATH is set to: {current_app.config.get('UPLOADS_FOLDER_PATH')}")
    
    VIDEO_FILE_PATH = osp.join(SESSION_FOLDER_PATH, filename)
    absolute_path = osp.abspath(VIDEO_FILE_PATH).replace("\\", "/")

    current_app.logger.debug(f"Absolute path to video: {absolute_path}")
    
    if not osp.exists(absolute_path):
        current_app.logger.error(f"File {filename} not found at path: {absolute_path}")
        flash('Video file not found. Please contact the administrator.')
        return redirect(url_for('core.index'))

    try:
        return send_file(absolute_path, as_attachment=True, download_name=filename)
    except Exception as e:
        current_app.logger.error(f"Error serving video: {e}")
        flash('Error serving video. Please contact the administrator.')
        return redirect(url_for('core.index'))
