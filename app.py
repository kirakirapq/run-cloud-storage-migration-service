from google.cloud import pubsub_v1
import json
import os
import subprocess
import time
import traceback


DESTINATION_BUCKET_NAME = os.getenv('DESTINATION_BUCKET_NAME')
PROJECT_ID = os.getenv('PROJECT_ID')
SUBSCRIPTION_ID = os.getenv('SUBSCRIPTION_ID')
OBJECT_FINALIZE = os.getenv('OBJECT_FINALIZE', 'OBJECT_FINALIZE')


def copyObjects(bucket_name: str, file_name: str, destination_bucket_name: str) -> dict:
    copy = "gsutil -m cp gs://{bucket}/{file} gs://{d_bucket}/".format(
        bucket=bucket_name,
        file=file_name,
        d_bucket=destination_bucket_name)

    try:

        check_res = subprocess.getoutput(copy)

        if ("completed" in check_res) == True:
            return {"is_success": True, "description": check_res}

        return {"is_success": False, "description": check_res}
    except Exception as e:
        return {"is_success": False, "description": traceback.format_exc()}


def summarize(message):
    # [START parse_message]
    data = message.data.decode("utf-8")
    attributes = message.attributes

    event_type = attributes["eventType"]
    bucket_id = attributes["bucketId"]
    object_id = attributes["objectId"]
    generation = attributes["objectGeneration"]
    description = (
        "\tEvent type: {event_type}\n"
        "\tBucket ID: {bucket_id}\n"
        "\tObject ID: {object_id}\n"
        "\tGeneration: {generation}\n"
    ).format(
        event_type=event_type,
        bucket_id=bucket_id,
        object_id=object_id,
        generation=generation,
    )

    if "overwroteGeneration" in attributes:
        description += "\tOverwrote generation: %s\n" % (
            attributes["overwroteGeneration"]
        )
    if "overwrittenByGeneration" in attributes:
        description += "\tOverwritten by generation: %s\n" % (
            attributes["overwrittenByGeneration"]
        )

    payload_format = attributes["payloadFormat"]
    if payload_format == "JSON_API_V1":
        object_metadata = json.loads(data)
        size = object_metadata["size"]
        content_type = object_metadata["contentType"]
        metageneration = object_metadata["metageneration"]
        description += (
            "\tContent type: {content_type}\n"
            "\tSize: {object_size}\n"
            "\tMetageneration: {metageneration}\n"
        ).format(
            content_type=content_type,
            object_size=size,
            metageneration=metageneration,
        )
    return {
        "event_type": event_type,
        "bucket_id": bucket_id,
        "object_id": object_id,
        "description": description
    }
    # [END parse_message]


def poll_notifications(project, subscription_name):
    """Polls a Cloud Pub/Sub subscription for new GCS events for display."""
    # [START poll_notifications]
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(
        project, subscription_name
    )

    def callback(message):
        summarize_response = summarize(message)
        event_type = summarize_response["event_type"]
        bucket_id = summarize_response["bucket_id"]
        object_id = summarize_response["object_id"]
        description = summarize_response["description"]

        print("Received message:\n{}".format(description))
        if event_type == OBJECT_FINALIZE:
            copy_response = copyObjects(
                bucket_id, object_id, DESTINATION_BUCKET_NAME)
            if copy_response['is_success'] is True:
                print("copy object to gs://{}/{}".format(object_id,
                                                         DESTINATION_BUCKET_NAME))
            else:
                print("object copy error:\n{}".format(
                    copy_response['description']))

        message.ack()

    subscriber.subscribe(subscription_path, callback=callback)

    # The subscriber is non-blocking, so we must keep the main thread from
    # exiting to allow it to process messages in the background.
    print("Listening for messages on {}".format(subscription_path))
    while True:
        time.sleep(60)
    # [END poll_notifications]


if __name__ == "__main__":
    print("start cloud run service.")
    poll_notifications(PROJECT_ID, SUBSCRIPTION_ID)
