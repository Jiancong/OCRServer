#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import request , jsonify, make_response
from flask_restful import Resource, reqparse, Api
import cv2
import numpy as np
import json, codecs
from restapi import tools
import logging
from restapi import recognize
import datetime
import os
import base64

import MySQLdb
import gc

HTTP_400_BAD_REQUEST = 400
HTTP_201_CREATED = 201
HTTP_200_SUCCESS = 200

TESS_CMD='tesseract'
RESULT_FOLDER = "./tmp"
ENCODING='ascii' 
UPLOAD_FOLDER = './images'

class GetTaskImageApi(Resource):
    def __init__(self, DB_HOST, DB_USER, DB_PASSWD, DB_NAME):
        self.db_host = DB_HOST
        self.db_user = DB_USER
        self.db_passwd = DB_PASSWD
        self.db_name = DB_NAME

    def get(self):
        parse = reqparse.RequestParser()
        parse.add_argument('task_id', type=str, required=True)

        args = parse.parse_args()

        task_id = args['task_id']

        # retrieve file type
        conn= MySQLdb.connect(self.db_host, self.db_user, self.db_passwd, self.db_name)
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT file_type from tasks where task_id =%s", (task_id, ))
            conn.commit()
            dataset = cursor.fetchall()

            # this task_id is not existed.
            if cursor.rowcount == 0:
                response_packet = {
                    "msg": 'Bad request.',
                    "ret": HTTP_400_BAD_REQUEST,
                    "data":{}
                }
                return make_response(jsonify(response_packet), HTTP_400_BAD_REQUEST)

            print('Total Row(s) fetched:', cursor.rowcount)

            for row in dataset:
                file_type = row[0]

        self.mFileType = file_type

        # return thumbnail picture for specific task_id
        filepath = UPLOAD_FOLDER+"/" + task_id + "_thumbnail." + self.mFileType
        print(filepath)

        with open(filepath, "rb") as image:
            image_b64encode_string = base64.b64encode(image.read())

        # result here: dict obj
        response_packet = {
            "msg": 'Access webpage success.',
            "ret": HTTP_200_SUCCESS,
            "data" : {
                "task_id": task_id,
                "file_type": self.mFileType,
                "imageb64": image_b64encode_string,
            }
        }

        return make_response(jsonify(response_packet), HTTP_200_SUCCESS) # <- the status_code displayed code on console



class DetectType3Api(Resource):
    def __init__(self, DB_HOST, DB_USER, DB_PASSWD, DB_NAME):
        self.db_host = DB_HOST
        self.db_user = DB_USER
        self.db_passwd = DB_PASSWD
        self.db_name = DB_NAME
    '''
    'ori_image': {
        # ori_w, ori_h is the origin image without any change (uploaded by wechat)
        'w': ori_image.shape[1],
        'h': ori_image.shape[0],
    },
    'normalize_image': {
        # w, h, file: normalized image (roate,resize, perspective)
        'w': int(perspective_img.shape[1]) if perspective_img is not None else None,
        'h': int(perspective_img.shape[0]) if perspective_img is not None else None,
        'file': compress_path,
        'extract_polygon': [{x: 100,y:200}, ..],        # here is a list of points which describe the polygon that wraps the normalized image
    },
    'type':{
        'name': cur_match_type_name,
        'desc': display name
        'value': orc_result,
        'roi': {
            'x': validate_roi_config['x'],
            'y': validate_roi_config['y'],
            'w': validate_roi_config['w'],
            'h': validate_roi_config['h'],
            'file': validate_roi_path
        }
    }

    '''
    def get(self):
        try:
            parse = reqparse.RequestParser()
            parse.add_argument('task_id', type=str, required=True)
            parse.add_argument('user_id', type=int, required=True)
            args = parse.parse_args()

            task_id = args['task_id']
            user_id = args['user_id']

            print("task_id=>", task_id, ",user_id=>", user_id)

            # retrieve file type from task_id
            conn= MySQLdb.connect(self.db_host, self.db_user, self.db_passwd, self.db_name)
            with conn:
                cursor = conn.cursor()

                cursor.execute("SELECT id from users where id = %s", (user_id, ))
                conn.commit()
                dataset = cursor.fetchall()
                if cursor.rowcount == 0:
                    raise ValueError("invalid user_id:", user_id)

                cursor.execute("SELECT file_type from tasks where task_id =%s ", (task_id, ))
                conn.commit()
                dataset = cursor.fetchall()
                # this task_id is not existed.
                if cursor.rowcount == 0:
                   raise ValueError("task_id is not existed.") 
                print('Total Row(s) fetched:', cursor.rowcount)

                for row in dataset:
                    file_type = row[0]

            self.mFileType = file_type

            if task_id and user_id and file_type:

                # attempt to retrieve info from backend directory.
                # bypass post2 if result exists.
                sdir = os.path.join(RESULT_FOLDER, task_id)
                if os.path.exists(sdir) and os.path.exists(os.path.join(sdir, 'response.json')):
                    print("path=>", sdir + "/response.json")
                    with open(os.path.join(sdir ,'response.json'), 'r') as file:
                        json_string = json.load(file)
                        response_packet = {
                                "msg": 'Success.',
                                "ret": HTTP_200_SUCCESS,
                                "data": json_string,
                                }
                        return make_response(jsonify(response_packet), HTTP_200_SUCCESS) # <- the status_code displayed code on console

                res = self.post2(task_id, UPLOAD_FOLDER)

                if res['code'] == HTTP_400_BAD_REQUEST:
                    raise ValueError('bad request in post2 query')
                else:
                    IMGDIR=os.path.join(RESULT_FOLDER, task_id, "step1")   

                    # do tesseract to recognize the docnumber and doctype
                    print("CMD=>", TESS_CMD + " " + RESULT_FOLDER +"/" + task_id + "/step1/roi-DocNumber.jpg" + " docnumres -l lancejie_fapiao3")
                    os.system(TESS_CMD + " " + RESULT_FOLDER + \
                            "/" + task_id + "/step1/roi-DocNumber.jpg" + " docnumres -l lancejie_fapiao3")
                    os.system(TESS_CMD + " " + RESULT_FOLDER + \
                            "/" + task_id + "/step1/roi-DocType.jpg" + " doctyperes -l lancejie_shuipiao2")

                    with open("docnumres.txt") as file:  
                        docnumres = file.read().rstrip()
                        print("docnumres=>", docnumres)

                    with open("doctyperes.txt") as file:
                        doctyperes = file.read().rstrip()
                        print("doctyperes=>", doctyperes)

                    with open(IMGDIR+"/roi-DocNumber.jpg", "rb") as image:
                        # base64 encode read data
                        # result: bytes
                        docnum_b64encode_bytes = base64.b64encode(image.read())
                        docnum_b64encode_string= docnum_b64encode_bytes.decode('utf-8')

                    with open(IMGDIR+"/roi-DocType.jpg", "rb") as image:
                        doctype_b64encode_bytes = base64.b64encode(image.read())
                        doctype_b64encode_string = doctype_b64encode_bytes.decode('utf-8')

                    conn = MySQLdb.connect(self.db_host, self.db_user, self.db_passwd, self.db_name)
                    with conn:
                        cursor = conn.cursor()
                        update_string = "UPDATE records SET invoice_code='{doctype}', InvoiceNum='{docnum}' where task_id = '{taskid}'".format(doctype=doctyperes, docnum=docnumres, taskid=task_id)
                        cursor.execute(update_string)
                        conn.commit()
                        print("update task_id=%s, doc_type=%s, doc_num=%s" % (task_id, doctyperes, docnumres))

                    response_data = {
                                "task_id": task_id,
                                "user_id": user_id,
                                "file_type": file_type,
                                "invoice_num": docnumres,
                                "invoice_code": doctyperes,
                                "invoice_num_encode": docnum_b64encode_string,
                                "invoice_code_encode": doctype_b64encode_string,
                            }

                    response_packet = {
                        "msg": 'Access webpage success.',
                        "ret": HTTP_200_SUCCESS,
                        "data" : response_data,
                    }
    
                    # store the parse result
                    with open(os.path.join(sdir, "response.json"), 'w') as outfile:
                        # now encoding the data into json
                        # result: string
                        json_data=json.dumps(response_data)
                        outfile.write(json_data)

                    return make_response(jsonify(response_packet), HTTP_200_SUCCESS) # <- the status_code displayed code on console
            else:
                raise ValueError("invalid user_id ,task_id or file_type", user_id, task_id, file_type)

        except ValueError as err:

            print(err.args)
            response_packet = {
                "msg": 'bad request.',
                "ret": HTTP_400_BAD_REQUEST,
                "data": {}
            }
            return make_response(jsonify(response_packet), HTTP_400_BAD_REQUEST) # <- the status_code displayed code on console

    def post2(self, strJobId, strFilePath):
        self.mStrJobID = strJobId
        self.mFilePath = strFilePath
        res = self.post()
        return res

    def post(self):
        #json_data = request.get_json(force=True)

        begin_time = datetime.datetime.now()

        logging.info('STEP ONE BEGIN')
        #logging.info('Request: %s' % str(json_data))

        #job_id = json_data['job_id']
        #file_path = json_data['file_path']

        job_id = self.mStrJobID
        openfilename = self.mFilePath + '/' + self.mStrJobID + '.' + self.mFileType
        print("openfilename=>", openfilename)

        if not os.path.isfile(openfilename):
            logging.error("The specified file is not found!")
            res = {
                    'code': HTTP_400_BAD_REQUEST,
                    'message': 'the file is not found!'
                }
            return res

        img = cv2.imread(openfilename, cv2.IMREAD_UNCHANGED)

        #if img == None :
        #    logging.error('the file not found!')
        #    res = {
        #            'code': 400,
        #            'message': 'the file is not found!'
        #        }   
        #    return res

        logging.info('Original image size : %s' % ((img.shape[1], img.shape[0]) ,))

        if img.shape[0] > 1500 or img.shape[1] > 1500:
            # if image is too big, resize to small one
            max_wh = max(img.shape[0], img.shape[1])
            k = max_wh / float(1280)

            img = cv2.resize(img, (int(img.shape[1] / k), int(img.shape[0] / k)), interpolation=cv2.INTER_AREA)
            logging.info('Image is too big, resize to small size = %s' % ((img.shape[1], img.shape[0]),))

        res = {
            'code': 0,
            'message': 'OK',
            'data': self.detectType(img, job_id)
        }

        logging.info('Response: %s' % str(res))
        logging.info('STEP ONE END, in %.2f seconds' % ((datetime.datetime.now() - begin_time).total_seconds(),))

        return res

    def make_error_response(self, ori_image):

        return {
            'ori_image': {
                'w': ori_image.shape[1],
                'h': ori_image.shape[0],
            },
            'normalize_image': None,
            'type': None
        }

    # detect image, find the right type in recognize configuration
    def detectType(self, image, job_id):
        config = recognize.getConfig()

        ############################################
        # 1. find matched type and config
        ############################################
        grey = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        logging.info("Start match...")

        # if multi-type is matched, using highest match rate as the matched one.
        # TODO: highest match rate is not preciseness, should be improved here

        cur_match_type_name = None
        cur_match_rate = -1
        cur_match_M = None
        cur_polygons = None

        logging.debug("Start match feature")

        sift = cv2.xfeatures2d.SIFT_create()
        ori_kp, ori_des = sift.detectAndCompute(grey, None)

        #logging.debug("config is %s" % str(config))

        for type_name in config:
            match_rate, detect_img, perspective_M, polygons = self.matchAndImageCut(sift, grey,
                                                                                    ori_kp, ori_des,
                                                                                    type_name,
                                                                                    config[type_name]['feature'],
                                                                                    config[type_name]['image'],
                                                                                    job_id)

            if match_rate > 0:
                logging.info("[%s] is matched, rate = %s" % (type_name, match_rate))
                tools.writeImageJob(detect_img, str(job_id) + '/step1', '1 match [%s] detect' % type_name)
                # tools.writeImageJob(cut_img, job_id + '/step1', '1 match [%s] cut' % type_name)

                if match_rate > cur_match_rate:
                    cur_match_rate = match_rate
                    cur_match_type_name = type_name
                    cur_match_M = perspective_M
                    cur_polygons = polygons

            else:
                logging.info("[%s] is not matched" % type_name)

        logging.debug("End match feature")

        print("cur_polygons =>", polygons)

        if not cur_match_type_name:
            logging.info("No feature matched")
            return self.make_error_response(image)

        logging.info("Match [%s] at %.2f%%, M=%s" % (cur_match_type_name, cur_match_rate, cur_match_M))

        ############################################
        # 2. rotate the image
        # TODO: should support different kinds of rotate/perspective way.
        ############################################
        cur_config = config[cur_match_type_name]
        perspective_img = None

        if cur_config['rotate'] == 'perspective':
            #print("image shape =>", image.shape)
	        #print("cur_config[image_w] =>", cur_config['image']['w'], 
		  #"cur_config[image_h] =>", cur_config['image']['h'])
            perspective_img = cv2.warpPerspective(image, cur_match_M,
                                                  (cur_config['image']['w'], cur_config['image']['h']),
                                                  flags=cv2.INTER_LANCZOS4)

	        #print("perspective_img.shape =>", perspective_img.shape)
            tools.writeImageJob(perspective_img, str(job_id) + '/step1', '2 perspective-%s' % cur_match_type_name)
        else:
            logging.error('rotate %s is not supported' % cur_config['rotate'])
            return self.make_error_response(image)

        # draw all roi in img
        perspective_draw_img = perspective_img.copy()
        for roiName in cur_config['roi']:
            tools.drawRoi(perspective_draw_img, cur_config['roi'][roiName], (0, 0, 255))

        tools.writeImageJob(perspective_draw_img, str(job_id) + '/step1', '3 mark roi')

        ############################################
        # 3. extract the validate area
        ############################################
        validate_roi_names = cur_config['validate']['roi']

        for validate_roi_name in validate_roi_names:
            validate_roi_config = cur_config['roi'].get(validate_roi_name, None)

            if not validate_roi_config:
                logging.error('Validate ROI[%s] not exist in roi section' % validate_roi_name)

            validate_roi, validate_roi_path = tools.createRoi2(perspective_img, validate_roi_name, validate_roi_config,
                                                           str(job_id) + '/step1')
            #ocr_result = tools.callOcr(validate_roi, job_id + '/step1', validate_roi_config)

            #logging.info('Validate ROI OCR result = %s' % ocr_result)

        return
        ############################################
        # 4. create compress jpg image
        ############################################
        compress_path = tools.writeImageJob(perspective_img, str(job_id) + '/step1', 'compressd', quality='compress')
        normlize_path = tools.writeImageJob(perspective_img, str(job_id) + '/step1', 'normlized', quality='lossless')

        ############################################
        # 5. write to yaml
        ############################################
        data = {
            'file': normlize_path,
            'type': cur_match_type_name
        }

        tools.saveJobData(data, str(job_id))

        logging.info('Save to data.yaml: %s' % str(data))

        return {
            'ori_image': {
                # ori_w, ori_h is the origin image without any change (uploaded by wechat)
                'w': image.shape[1],
                'h': image.shape[0],
            },
            'normalize_image': {
                # w, h, file: normalized image (roate,resize, perspective)
                'w': int(perspective_img.shape[1]) if perspective_img is not None else None,
                'h': int(perspective_img.shape[0]) if perspective_img is not None else None,
                'file': compress_path,
                'extract_polygon': cur_polygons,
            },
            # the detected image type and its value based, the roi is based on normalized image
            # if not match, set None
            'type': {
                'name': cur_match_type_name,
                'desc': cur_config.get('name', cur_match_type_name),
                'value': orc_result,
                'roi': {
                    'x': validate_roi_config['x'],
                    'y': validate_roi_config['y'],
                    'w': validate_roi_config['w'],
                    'h': validate_roi_config['h'],
                    'file': validate_roi_path
                }
            }
        }

        # return {
        #     'image': {
        #         # w, h, file: normalized image (roate,resize, perspective)
        #         'w': perspective_img.shape[1],
        #         'h': perspective_img.shape[0],
        #         'file': compress_path,
        #
        #         # ori_w, ori_h is the origin image without any change (uploaded by wechat)
        #         'ori_w': image.shape[1],
        #         'ori_h': image.shape[0],
        #
        #         # TODO: add polyline points which wrapper the image
        #     },
        #     # the detected image type and its value based, the roi is based on normalized image
        #     # if not match, set None
        #     'type': {
        #         'name': cur_match_type_name,
        #         'value': orc_result,
        #         'roi': {
        #             'x': validate_roi_config['x'],
        #             'y': validate_roi_config['y'],
        #             'w': validate_roi_config['w'],
        #             'h': validate_roi_config['h'],
        #             'file': validate_roi_path
        #         }
        #     }
        # }

    def matchAndImageCut(self, sift, origin, ori_kp, ori_des, typeName, featureConfig, imageConfig, job_id):
        # TODO: check file exists
        img_template = cv2.imread(featureConfig['file'], cv2.IMREAD_GRAYSCALE)

        img_detect = origin.copy()

        min_match_count = featureConfig['option'].get('minMatchCount', 50)
        distance_threshold = featureConfig['option'].get('matchDistance', 0.5)

        tpl_kp, tpl_des = sift.detectAndCompute(img_template, None)

        index_params = dict(algorithm=0, trees=5)  # algorithm = FLANN_INDEX_KDTREE
        search_params = dict(checks=50)

        flann = cv2.FlannBasedMatcher(index_params, search_params)

        matches = flann.knnMatch(tpl_des, ori_des, k=2)

        # store all the good matches as per Lowe's ratio test.
        good = []
        for m, n in matches:
            if m.distance < distance_threshold * n.distance:
                good.append(m)

        logging.info("Feature [%s] matches %s, min=%s, threshold=%.2f, good=%s" % (
            typeName, len(matches), min_match_count, distance_threshold, len(good)))


        if len(good) > min_match_count:
            src_pts = np.float32([tpl_kp[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
            dst_pts = np.float32([ori_kp[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

            M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

            # draw feature polyline in origin image
            pts = np.float32([[0, 0], [0, img_template.shape[0] - 1],
				      [img_template.shape[1] - 1, img_template.shape[0] - 1],
				      [img_template.shape[1] - 1, 0]]).reshape(-1, 1, 2)
            dst = cv2.perspectiveTransform(pts, M)

            cv2.polylines(img_detect, [np.int32(dst)], True, 0, 3)

            # draw detected image
            matchesMask = mask.ravel().tolist()
            draw_params = dict(matchColor=(0, 255, 0),  # draw matches in green color
                               singlePointColor=None,
                               matchesMask=matchesMask,  # draw only inliers
                               flags=2)

            draw_img = cv2.drawMatches(img_template, tpl_kp, origin, ori_kp, good, None, **draw_params)
            tools.writeImageJob(draw_img, str(job_id) + '/step1', 'draw matching %s' % typeName)

            # draw normalize image's polyline in origin image
            normalized_pts = np.float32([
                [-1 * featureConfig['x'], -1 * featureConfig['y']],
                [-1 * featureConfig['x'], imageConfig['h'] - featureConfig['y'] - 1],
                [imageConfig['w'] - featureConfig['x'] - 1, imageConfig['h'] - featureConfig['y'] - 1],
                [imageConfig['w'] - featureConfig['x'] - 1, -1 * featureConfig['y']]]) \
                .reshape(-1, 1, 2)
	    #print("normalized_pts =>", normalized_pts)

            normalized_dst = cv2.perspectiveTransform(normalized_pts, M)
	    #print("normalized_pts after perspectiveTransform =>", normalized_dst)
            cv2.polylines(img_detect, [np.int32(normalized_dst)], True, 255, 3)

            # add offset to src_pts so that it can create right matrix
            for p in src_pts:
                p[0][0] += featureConfig.get('x', 0)
                p[0][1] += featureConfig.get('y', 0)

	    #print("src_pts =>", src_pts)
	    #print("dst_pts =>", dst_pts)
            M2, mask2 = cv2.findHomography(dst_pts, src_pts, cv2.RANSAC, 5.0)

            normalized_polygons = []
            for d in np.int32(normalized_dst).tolist():
                normalized_polygons.append({
                    'x': d[0][0],
                    'y': d[0][1]
                })

            return float(len(good)) / float(len(matches)), img_detect, M2, normalized_polygons
        else:
            return 0, None, None, None

#if __name__ == '__main__':
#    detect = DetectType2Api()
#    detect.post()
