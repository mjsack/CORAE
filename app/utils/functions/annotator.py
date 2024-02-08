import json
import os
import random

import ffmpeg
from flask import current_app, flash, redirect, url_for
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.utils import secure_filename

from ...models import Annotation, Participant, Video, ParticipantVideoAssociation
from ..extensions import db


def extract_video_properties(video_path):
    """
    Extracts the frame rate and duration of a video using ffmpeg.

    Args:
    - video_path (str): Path to the video file.

    Returns:
    - float: Frame rate of the video.
    - float: Duration of the video in seconds.
    """
    try:
        probe = ffmpeg.probe(video_path)
        stream_data = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        r_frame_rate = stream_data['r_frame_rate']
        num, denom = map(int, r_frame_rate.split('/'))
        frame_rate = num / denom

        duration = float(stream_data['duration'])
        
        return frame_rate, duration

    except Exception as e:
        current_app.logger.error(f"Error extracting video properties using FFmpeg for video: {video_path}. Error: {e}")
        return None, None
        
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
            for participant, video in zip(participants, videos):
                assoc = get_or_create_association(participant, video)
                assoc.owner = True
                db.session.add(assoc)

        for participant in participants:
            for video in videos:
                if coupling == "coupled" and any(assoc.owner and assoc.video == video for assoc in participant.video_associations):
                    continue
                assoc = get_or_create_association(participant, video)
                db.session.add(assoc)

        if ordering == "random":
            for participant in participants:
                participant_videos = [assoc.video for assoc in participant.video_associations if not assoc.owner]
                random.shuffle(participant_videos)
                for index, video in enumerate(participant_videos):
                    assoc = get_or_create_association(participant, video)
                    assoc.order = index + 1
                    db.session.add(assoc)

        db.session.commit()

    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error during video-participant association: {e}")
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
        annotations_data_dict = data.get('annotations')

        for video_id_str, annotations_list in annotations_data_dict.items():
            video_id = int(video_id_str)
            video = Video.query.get(video_id)
            if video is None:
                current_app.logger.error(f"Video with ID {video_id} not found in the database.")
                continue

            for annotation_data in annotations_list:
                existing_annotation = Annotation.query.filter_by(
                    participant_id=participant.id,
                    video_id=video.id,
                    timecode=annotation_data["timestamp"],
                    frame_number=annotation_data["video_frame"]
                ).first()
                if existing_annotation:
                    continue  # Skip duplicate entry
                annotation = Annotation(
                    timecode=annotation_data["timestamp"],
                    frame_number=annotation_data["video_frame"],
                    slider_position=annotation_data["slider_position"],
                    participant_id=participant.id,
                    video_id=video.id
                )
                db.session.add(annotation)

        participant.has_submitted = True
        db.session.commit()

        current_app.logger.info(f"Annotations saved successfully for participant ID: {participant.id}")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error saving annotations: {e}")
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
    
    video_instance = Video()
    video_instance.tokenize()
    
    extension = os.path.splitext(secure_filename(video.filename))[1]
    
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
    frame_rate, duration = extract_video_properties(absolute_path_after)
    current_app.logger.info(f"Extracted frame rate: {frame_rate}, Duration: {duration}")

    video_instance.filename = filename
    video_instance.filepath = VIDEO_FILE_PATH
    video_instance.frame_rate = frame_rate
    video_instance.duration = duration
    db.session.add(video_instance)
    db.session.commit()

    return filename