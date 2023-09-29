from flask import (Blueprint, current_app, flash, jsonify, redirect,
                   render_template, request, url_for)
from flask_login import current_user, login_required
from sqlalchemy.exc import SQLAlchemyError

from ..forms import SessionCreateForm
from ..models import (Participant, Project, Session, Video,
                      participant_video_association)
from ..utils.extensions import db
from ..utils.functions.annotator import (assign_and_order_videos,
                                         get_or_create_association,
                                         participant_annotations_to_json,
                                         save_video_to_disk)
from ..utils.functions.common import toggle_item_status
from ..utils.functions.validation import validate_project_owner

sessions = Blueprint('sessions', __name__)

@sessions.route('/sessions/<int:project_id>/new', methods=['GET', 'POST'])
@login_required
def new_session(project_id):
    """
    Create a new session for a given project.

    Parameters:
    - project_id (int): ID of the project for which the session is being created.

    Returns:
    - Response: Redirects to the project view after session creation.
    """
    try:
        current_app.logger.info(f"Creating a new session for project ID: {project_id}")
        project = Project.query.get_or_404(project_id)
        form = SessionCreateForm(capacity=project.settings.capacity)
        
        if request.method == 'GET':
            return render_template('admin/sessions/new_session.html', title='New Session', header=project.name, subheader='New Session', form=form, coupling=project.settings.coupling)

        if form.validate_on_submit():
            new_session = Session(project_id=project_id, description="New Session")
            new_session.tokenize()
            db.session.add(new_session)
            for field in form.participants:
                participant_name = field.data
                participant_instance = Participant(name=participant_name)
                participant_instance.tokenize()
                db.session.add(participant_instance)
                new_session.participants.append(participant_instance)
            uploaded_videos = []
            if project.settings.coupling == "coupled":
                for idx, participant in enumerate(form.participants):
                    video_file = form.videos[idx].data
                    filename = save_video_to_disk(video_file, project_id, new_session.id)
                    video = Video.query.filter_by(filename=filename).first()
                    uploaded_videos.append(video)
                    
                    assoc = get_or_create_association(new_session.participants[idx], video)
                    assoc.owner = True
                    db.session.add(assoc)

            elif project.settings.coupling == "decoupled":
                uploaded_files = request.files.getlist('general_videos')
                for video_file in uploaded_files:
                    filename = save_video_to_disk(video_file, project_id, new_session.id)
                    uploaded_videos.append(Video.query.filter_by(filename=filename).first())

            assign_and_order_videos(new_session.participants, uploaded_videos, project.settings.coupling, project.settings.ordering)

            for participant in new_session.participants:
                if not participant.videos:
                    current_app.logger.error(f"Participant {participant.name} does not have any videos assigned. This should not happen.")
                    flash(f"Participant {participant.name} does not have any videos assigned. Please ensure all participants have videos.")
                    return redirect(url_for('projects.view_project', project_id=project_id))
                else:
                    current_app.logger.debug(f"Participant {participant.name} has {len(participant.videos)} videos assigned.")

            db.session.commit()
            current_app.logger.info(f"Session created successfully for project ID: {project_id}")
            flash('Session created successfully.')
        else:
            missing_names = [f"Participant {i+1}" for i, participant in enumerate(form.participants.entries) if not participant.name]
            if missing_names:
                flash(f"Names are required for: {', '.join(missing_names)}", 'error')
            else:
                flash('Form validation failed. Please check the input data.', 'error')

    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error creating session for project ID: {project_id}. Error: {str(e)}")
        flash('Database error while creating session. Please try again.', 'error')
    except Exception as e:
        current_app.logger.error(f"Error creating session for project ID: {project_id}. Error: {str(e)}")
        flash('Error creating session. Please try again.', 'error')

    return redirect(url_for('projects.view_project', project_id=project_id))


@sessions.route('/sessions/<int:project_id>/<int:session_id>', methods=['GET', 'POST'])
@login_required
def view_session(project_id, session_id):
    """
    View details of a specific session.

    Parameters:
    - project_id (int): ID of the project.
    - session_id (int): ID of the session to view.

    Returns:
    - Rendered Template: Displays the session details.
    """
    session = Session.query.get_or_404(session_id)
    project = Project.query.get_or_404(project_id)
    
    # If the session does not exist, redirect to the dashboard
    if not session:
        flash('Session not found.', 'danger')
        return redirect(url_for('dashboard'))

    # Fetch participants associated with the session
    participants = Participant.query.filter_by(session_id=session.id).all()

    # Fetch videos associated with each participant
    participant_videos = {}
    for participant in participants:
        participant_videos[participant.id] = db.session.query(Video).join(
            participant_video_association, Video.id == participant_video_association.c.video_id
        ).filter(participant_video_association.c.participant_id == participant.id).all()

    form = SessionCreateForm(capacity=len(participants))
    
    for i, participant in enumerate(participants):
        form.participants[i].data = participant.name
        # Ensure there's a VideoForm instance for this participant
        while len(form.videos) <= i:
            form.videos.append_entry()
        # Set the video data
        if participant_videos[participant.id]:
            form.videos[i].data = participant_videos[participant.id][0].filename

    return render_template('admin/sessions/view_session.html', title='Session', header=project.name, session=session, form=form, participants=participants, participant_videos=participant_videos, project_id=project_id)

@sessions.route('/sessions/<int:project_id>/<int:session_id>/archived', methods=['POST'])
@login_required
def toggle_session_status(project_id, session_id):
    """
    Toggle the status (active/archived) of a session.

    Parameters:
    - project_id (int): ID of the project.
    - session_id (int): ID of the session to toggle.

    Returns:
    - Response: Redirects to the project view after toggling the session status.
    """
    toggle_item_status('session', session_id)
    return redirect(url_for('projects.view_project', project_id=project_id))

@sessions.route('/sessions/<int:project_id>/<int:session_id>/upload', methods=['POST'])
@login_required
def upload_video(project_id, session_id):
    """
    Upload a video for a specific session.

    Parameters:
    - project_id (int): ID of the project.
    - session_id (int): ID of the session for which the video is being uploaded.

    Returns:
    - Response: Redirects to the project view after video upload.
    """
    current_app.logger.info(f"Uploading video for project ID: {project_id} and session ID: {session_id}")
    validate_project_owner(project_id)
    video_file = request.files['video']
    filename = save_video_to_disk(video_file, project_id, session_id)
    if filename:
        current_app.logger.info(f"Video {filename} uploaded successfully for project ID: {project_id} and session ID: {session_id}")
        return redirect(url_for('projects.view_project'))
    current_app.logger.warning(f"Failed to upload video for project ID: {project_id} and session ID: {session_id}")
    return redirect(url_for('projects.view_project'))

@sessions.route('/sessions/<int:session_id>/download/<token>', methods=['GET'])
@login_required
def download_participant_data(session_id, token):
    """
    Download annotations for a participant based on a token.

    Parameters:
    - session_id (int): ID of the session.
    - token (str): Token of the participant.

    Returns:
    - JSON Response: Annotations data for the participant.
    """
    current_app.logger.info(f"Downloading annotations for participant with token: {token} in session ID: {session_id}")
    participant_instance = Participant.query.filter_by(token=token).first_or_404()
    session = Session.query.get_or_404(session_id)
    project_instance = session.project

    # Ensure the project belongs to the current user
    if project_instance.researcher != current_user:
        flash('You do not have access to this session.', 'error')
        return redirect(url_for('dashboard.dash'))

    # Check if the participant belongs to the given session.
    if participant_instance.session.id != session_id:
        flash('Mismatch between session and participant.', 'error')
        return redirect(url_for('dashboard.dash'))

    # Use the helper method to convert the participant's annotations to JSON format
    annotation_data = participant_annotations_to_json(participant_instance)
    
    # Use Flask's jsonify to return the data with the right headers for downloading
    response = jsonify(annotation_data)
    response.headers.set('Content-Disposition', 'attachment', filename=f'participant_{participant_instance.id}_annotations.json')
    return response

@sessions.route('/sessions/<int:session_id>/download/aggregate', methods=['GET'])
@login_required
def download_aggregate_data(session_id):
    """
    Download aggregate data for a session.

    Parameters:
    - session_id (int): ID of the session.

    Returns:
    - JSON Response: Aggregate data for the session.
    """
    current_app.logger.info(f"Downloading aggregate data for session ID: {session_id}")
    session = Session.query.get_or_404(session_id)
    
    # Loop through the participants and collect their data
    participants_data = []
    for participant in session.participants:
        participants_data.append(participant_annotations_to_json(participant))
    
    session_data = {
        'Session ID': session.id,
        'Description': session.description,
        'Number of Participants': len(session.participants),
        'Participants Data': participants_data
    }
    
    response = jsonify(session_data)
    response.headers.set('Content-Disposition', 'attachment', filename=f'session_{session_id}_aggregate.json')
    return response