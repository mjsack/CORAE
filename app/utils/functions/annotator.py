import json
import os
import random

import ffmpeg
from flask import current_app, flash, redirect, url_for
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.utils import secure_filename

from ...models import Annotation, Participant, Video, ParticipantVideoAssociation
from ..extensions import db


def extract_frame_rate(video_path):
    """
    Extracts the frame rate of a video using ffmpeg-python.

    Args:
    - video_path (str): Path to the video file.

    Returns:
    - float: Frame rate of the video.
    """
    current_app.logger.debug(f"Starting frame rate extraction for video: {video_path}")
    try:
        probe = ffmpeg.probe(video_path)
        current_app.logger.debug(f"FFmpeg probe result: {json.dumps(probe, indent=2)}")
        
        stream_data = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        current_app.logger.debug(f"Video stream data: {json.dumps(stream_data, indent=2)}")

        r_frame_rate = stream_data['r_frame_rate']
        num, denom = map(int, r_frame_rate.split('/'))
        frame_rate = num / denom
        return frame_rate

    except ffmpeg.Error as e:
        current_app.logger.error(f"Error extracting frame rate using FFmpeg for video: {video_path}. Error: {e}")
        return None
    except Exception as e:
        current_app.logger.error(f"Unexpected error during frame rate extraction for video: {video_path}. Error: {e}")
        return None
    finally:
        current_app.logger.debug(f"Finished frame rate extraction for video: {video_path}")
        
def get_or_create_association(participant, video):
    """
    Retrieves or creates an association between a participant and a video.

    Args:
    - participant (Participant): The participant instance.
    - video (Video): The video instance.

    Returns:
    - ParticipantVideoAssociation: The association between the participant and the video.
    """
    association = ParticipantVideoAssociation.query.filter_by(
        participant_id=participant.id, video_id=video.id).first()
    if not association:
        association = ParticipantVideoAssociation(video=video, participant=participant)
    return association

def assign_and_order_videos(participants, videos, coupling, ordering):
    """
    Assigns and orders videos for participants based on the coupling and ordering conditions.

    Args:
    - participants (list): List of participant instances.
    - videos (list): List of video instances.
    - coupling (str): The coupling condition ("coupled" or other).
    - ordering (str): The ordering condition ("random" or other).
    """
    current_app.logger.debug(f"Number of participants: {len(participants)}, Number of videos: {len(videos)}")
    
    try:
        if coupling == "coupled":
            for i, participant in enumerate(participants):
                owned_video = videos[i]
                assoc = get_or_create_association(participant, owned_video)
                assoc.owner = True
                db.session.add(assoc)
                current_app.logger.debug(
                    f"Set owner relationship for video ID: {owned_video.id} and participant ID: {participant.id}")

        for participant in participants:
            for video in videos:
                # Skip if this is an owned video in the coupled condition
                if coupling == "coupled" and video in participant.videos:
                    continue
                
                get_or_create_association(participant, video)
                current_app.logger.debug(
                    f"Associating video ID: {video.id} with participant ID: {participant.id}")


        if ordering == "random":
            for participant in participants:
                random.shuffle(participant.videos)

                for index, video in enumerate(participant.videos):
                    assoc = get_or_create_association(participant, video)
                    assoc.order = index + 1
                    db.session.add(assoc)

        for participant in participants:
            associated_video_ids = [video.id for video in participant.videos]
            current_app.logger.debug(
                f"Participant ID: {participant.id} associated with video IDs: {associated_video_ids}")

        db.session.commit()

    except SQLAlchemyError as e:
        current_app.logger.error(f"Error during video-participant association: {e}")
        db.session.rollback()
        raise
    except Exception as e:
        current_app.logger.error(f"Unexpected error during video-participant association: {e}")
        raise

def save_annotations(request, participant):
    """
    Saves annotations for a participant based on the request data.

    Args:
    - request (Request): The Flask request object containing the annotation data.
    - participant (Participant): The participant instance.

    Returns:
    - Response: A Flask response object.
    """
    try:
        current_app.logger.info(f"Saving annotations for participant ID: {participant.id}")
        data = request.get_json()
        video_id = data.get('video_id')
        
        annotations_data_dict = data.get('annotations')
        if not video_id and annotations_data_dict:
            video_id = list(annotations_data_dict.keys())[0]
            
        current_app.logger.info(f"Value for 'video_id' assigned as: {video_id}")

        video = Video.query.get(video_id)
        if video is None:
            error_message = f"Video with ID {video_id} not found in the database."
            current_app.logger.error(error_message)
            flash(error_message, 'danger')
            return redirect(url_for('core.index'))

        for video_id_key, annotations_list in annotations_data_dict.items():
            for annotation_data in annotations_list:
                annotation = Annotation(
                    participant_id=participant.id,
                    video_id=video.id,
                    timecode=annotation_data["timestamp"],
                    frame_number=annotation_data["video_frame"],
                    slider_position=annotation_data["slider_position"]
                )
                db.session.add(annotation)

        progress = request.form.get('progress', 0.0)
        if 0 <= float(progress) <= 100:
            participant.progress = float(progress)

        db.session.commit()
        current_app.logger.info(f"Annotations saved successfully for participant ID: {participant.id} and video ID: {video_id}")
        participant.has_submitted = True
        flash('Thank you for completing the annotations!')
    except Exception as e:
        current_app.logger.error(f"Error saving annotations: {e}")
        current_app.logger.debug(f"Problematic data: {request.data}")
        flash('There was an error saving your annotations. Please try again.', 'danger')
    finally:
        return redirect(url_for('core.index'))
        
def participant_annotations_to_json(participant):
    """
    Converts a participant's annotations to a JSON format.

    Args:
    - participant (Participant): The participant instance.

    Returns:
    - dict: A dictionary containing the participant's annotations in JSON format.
    """
    session = get_session_from_participant(participant)
    project = get_project_from_participant(participant)
    participant_data = {
        "participant_external_id": participant.name,
        "participant_internal_id": participant.id,
        "project_id": project.id,
        "project_token": project.token,
        "session_id": session.id,
        "session_token": session.token,
        "participant_token": participant.token,
        "videos": []
    }
       
    for video in participant.videos:
        annotations = Annotation.query.filter_by(participant_id=participant.id, video_id=video.id).all()
        annotations_data = [{
            "timecode": annotation.timecode,
            "frame_number": annotation.frame_number,
            "slider_position": annotation.slider_position
        } for annotation in annotations]
        
        video_data = {
            "video_id": video.id,
            "duration": video.duration,
            "frame_rate": video.frame_rate,
            "annotations": annotations_data
        }
        
        participant_data["videos"].append(video_data)
        current_app.logger.debug(f"Participant data before JSON serialization: {participant_data}")

    return participant_data


def update_participant_progress(participant_id, progress_value):
    """
    Updates the progress of a participant.

    Args:
    - participant_id (int): The ID of the participant.
    - progress_value (float): The progress value to set (between 0 and 100).

    Returns:
    - dict: A dictionary containing a message about the update status.
    - int: HTTP status code.
    """
    if 0 <= float(progress_value) <= 100:
        participant_instance = Participant.query.get_or_404(participant_id)
        participant_instance.progress = progress_value
        db.session.commit()
        return {'message': 'Progress updated successfully'}, 200
    else:
        return {'message': 'Invalid progress value'}, 400
    
def get_session_from_participant(participant_instance):
    """
    Retrieves the session associated with a participant.

    Args:
    - participant_instance (Participant): The participant instance.

    Returns:
    - Session: The session associated with the participant.
    """
    session = participant_instance.session
    if not session:
        current_app.logger.warning(f"No session associated with token: {participant_instance.token}")
        flash('The session associated with this link is not available.')
        return redirect(url_for('core.index'))
    return session

def get_project_from_participant(participant_instance):
    """
    Retrieves the project associated with a participant.

    Args:
    - participant_instance (Participant): The participant instance.

    Returns:
    - Project: The project associated with the participant.
    """
    project = participant_instance.session.project
    if not project:
        current_app.logger.warning(f"No project associated with token: {participant_instance.token}")
        flash('The project associated with this link is not available.')
        return redirect(url_for('core.index'))
    return project

def save_video_to_disk(video, project_id, session_id):
    """
    Saves a video file to the disk and updates the corresponding video instance.

    Args:
    - video (FileStorage): The video file to save.
    - project_id (int): The ID of the project.
    - session_id (int): The ID of the session.

    Returns:
    - str: The filename of the saved video.
    """
    current_working_directory = os.getcwd()
    current_app.logger.debug(f"Current working directory: {current_working_directory}")
    SESSION_FOLDER_PATH = os.path.join(current_app.config.get('UPLOADS_FOLDER_PATH'), str(project_id), str(session_id))
    try:
        if not os.path.exists(SESSION_FOLDER_PATH):
            current_app.logger.debug(f"{SESSION_FOLDER_PATH} does not exist. Creating directory.")
            os.makedirs(SESSION_FOLDER_PATH)
        else:
            current_app.logger.debug(f"{SESSION_FOLDER_PATH} already exists. Skipping directory creation.")
    except Exception as e:
        current_app.logger.error(f"Error creating directory {SESSION_FOLDER_PATH}: {e}")
        raise
    
    # Create a Video instance and generate a token for it
    video_instance = Video()
    video_instance.tokenize()
    
    # Extract the file extension from the original filename
    extension = os.path.splitext(secure_filename(video.filename))[1]
    
    # Construct the new filename using the token and the extracted extension
    filename = f"{video_instance.token}{extension}"
    
    VIDEO_FILE_PATH = os.path.join(SESSION_FOLDER_PATH, filename)
    current_app.logger.info(f"Attempting to save video to {VIDEO_FILE_PATH}")
    absolute_path_before = os.path.abspath(VIDEO_FILE_PATH).replace("\\", "/")
    current_app.logger.debug(f"Absolute path before saving video: {absolute_path_before}")

    video.save(VIDEO_FILE_PATH)
    current_app.logger.debug(f"Saved video with filename: {filename} at path: {VIDEO_FILE_PATH}")

    absolute_path_after = os.path.abspath(VIDEO_FILE_PATH).replace("\\", "/")
    current_app.logger.debug(f"Absolute path after saving video: {absolute_path_after}")

    video_size = os.path.getsize(VIDEO_FILE_PATH)
    current_app.logger.debug(f"Video size on disk: {video_size} bytes")
    
    current_app.logger.info(f"Attempting to extract frame rate from {absolute_path_after}")
    frame_rate = extract_frame_rate(absolute_path_after)  # Then, extract the frame rate
    current_app.logger.info(f"Extracted frame rate: {frame_rate}")

    # Update the Video instance attributes
    video_instance.filename = filename
    video_instance.filepath = VIDEO_FILE_PATH
    video_instance.frame_rate = frame_rate  # Set the extracted frame rate
    db.session.add(video_instance)
    db.session.commit()

    return filename