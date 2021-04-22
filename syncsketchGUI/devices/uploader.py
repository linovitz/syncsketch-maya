import logging
import webbrowser
import os

from pprint import pformat

from ..lib import database
from ..lib import user
from ..lib import path

from ..lib.gui import qt_dialogs #Remove QT dependency

logger = logging.getLogger("syncsketchGUI")


def upload(open_after_upload = None, show_success_msg = False):

    logger.info("open_after_upload Url: {}".format(open_after_upload))
    uploaded_item = _upload()


    if not uploaded_item:
        return

    if open_after_upload is None:
        open_after_upload = True if database.read_cache('ps_open_afterUpload_checkBox') == 'true' else False

    if open_after_upload:
        url = path.make_url_offlineMode(uploaded_item['reviewURL'])
        logger.info("Url: {}".format(url))
        logger.info("Uploaded Item: {}".format(uploaded_item))
        logger.info("Opening Url: {}".format(uploaded_item['reviewURL']))
        webbrowser.open(url, new=2, autoraise=True)


    if not open_after_upload:
        logger.info("uploaded_item: {}".format(uploaded_item))
        _show_success_message(path.make_url_offlineMode(uploaded_item['reviewURL']))

    return uploaded_item

def _upload(current_user=None, ):
    errorLog = None
    if not current_user:
        current_user = user.SyncSketchUser()
    username = current_user.get_name()
    upload_file = _get_current_file()

    if not upload_file or not os.path.isfile(upload_file):
        return

    # Try to upload to the last uploaded address first
    selected_item = database.read_cache('treewidget_selection')
    logger.info("selected_item: {0}".format(selected_item))


    # ToDo rename media_id to item_id
    item_type = database.read_cache('target_url_type')
    review_id = database.read_cache('target_review_id')
    item_id = database.read_cache('target_media_id')
    item_name = database.read_cache('target_url_item_name')

    # Upload To
    current_item = selected_item
    upload_to_value = item_name
    logger.info('Selected Item: %s'%item_name)


    last_recorded_data = database.read_cache('last_recorded')

    postData = {
        "first_frame": last_recorded_data['start_frame'],
        "last_frame": last_recorded_data['end_frame'],
    }


    if item_type == 'review':
        logger.info('Uploading {} to {} with review_id {}'.format(upload_file, upload_to_value, review_id))
        uploaded_item = current_user.upload_media_to_review(review_id, upload_file, noConvertFlag = True, itemParentId = False, data = postData)
        #logger.info("uploaded_item: {0}".format(pformat(uploaded_item)))

    elif item_type == 'media':
        logger.info('Updating item {} with file {}'.format(upload_to_value, upload_file))
        logger.info("item id %s"%item_id)
        logger.info("filepath %s"%upload_file)
        logger.info("Trying to upload %s to item_id %s, review %s"%(upload_file,item_id,review_id))
        uploaded_item = current_user.upload_media_to_review(review_id, upload_file, noConvertFlag = True, itemParentId = item_id, data = postData)
        logger.info(pformat(uploaded_item))
    else:
        uploaded_item = None
        errorLog = 'You cannot upload to %s "%s" directly.\nPlease select a review in the tree widget to upload to!\n'%(item_type, item_name)

    if not uploaded_item:
        if not errorLog:
            errorLog = 'No Uploaded Item returned from Syncsketch'

        logger.info('ERROR: This Upload failed: %s'%(errorLog))
        return

    # * this is an old call, that we should replace with an async worker
    review_data = current_user.get_review_data_from_id(review_id)


    review_url = review_data.get('reviewURL')
    #uploaded_media_url = '{}'.format(review_url)
    uploaded_media_url = '{}#{}'.format(review_url, uploaded_item['id'])
    logger.info("review_data: {}".format(review_data))
    logger.info('Upload successful. Uploaded item {} to {}'.format(upload_file, uploaded_media_url))

    if 'none' in uploaded_media_url.lower():
        uploaded_media_url = ""

    uploaded_item['reviewURL'] = uploaded_media_url
    return uploaded_item


def _show_success_message(uploaded_item):
    # todo: add offlineMode here as well
    title = 'Upload Successful'
    info_message = 'Your file has successfully been uploaded. Please follow this link:'

    UploadedMediaDialog = qt_dialogs.InfoDialog(None,
                                          title,
                                          info_message,
                                          uploaded_item)
    UploadedMediaDialog.exec_()


def _get_current_file():
    # validate file name
    filename = database.read_cache('last_recorded_selection')

    if not filename:
        title = 'No File for Upload'
        message = 'There is no previously recorded video file, please record one first through The Widget'
        qt_dialogs.WarningDialog(None, title, message)
        return


    filename = path.sanitize(filename)

    if not os.path.isfile(filename):
        title = 'Not a valid file'
        message = 'Please provide a valid file'
        logger.debug("{} is not a valid file".format(filename))
        qt_dialogs.WarningDialog(None, title, message)
        return
    else:
        return filename