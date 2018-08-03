#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import request , jsonify, make_response
from flask_restful import Resource, reqparse, Api

import MySQLdb
import gc
import json

HTTP_202_ACCEPTED = 202

class InsertRecordApi(Resource):
    def __init__(self, DB_HOST, DB_USER, DB_PASSWD, DB_NAME):
        self.db_host = DB_HOST
        self.db_user = DB_USER
        self.db_passwd = DB_PASSWD
        self.db_name = DB_NAME

    def post(self):
        try:
            parse = reqparse.RequestParser()
            parse.add_argument('user_id', type=int, required=True)
            parse.add_argument('task_id', type=str, required=True)
            parse.add_argument('file_type', type=str, required=True)
            args = parse.parse_args()
            user_id = args['user_id']
            task_id = args['task_id']
            file_type = args['file_type']
            print("user_id=>", user_id, ",task_id=>", task_id, ", file_type=>", file_type)

            if user_id and task_id:
                conn = MySQLdb.connect(self.db_host, self.db_user, self.db_passwd, self.db_name)
                with conn:
                    cursor = conn.cursor() 
                    cursor.execute('INSERT INTO tasks (task_id, file_type) values(%s, %s)', 
                                    [task_id, file_type])
                    conn.commit()

                    cursor.execute('INSERT INTO records (user_id, task_id ) values(%s, %s)',
                                    [user_id, task_id])
                    conn.commit()
                    print(cursor.rowcount, " record inserted.")
                    cursor.close()
                    
                    gc.collect()

                    return {'ret':HTTP_202_ACCEPTED,'msg': 'Success'}

        except Exception as e:
            return {'error': str(e)}


class FetchRecordsApi(Resource):
    def __init__(self, DB_HOST, DB_USER, DB_PASSWD, DB_NAME):
        self.db_host = DB_HOST
        self.db_user = DB_USER
        self.db_passwd = DB_PASSWD
        self.db_name = DB_NAME

    def get(self):
        try:
            parse = reqparse.RequestParser()
            parse.add_argument('user_id', type=int, required=True)
            args = parse.parse_args()
            user_id = args['user_id']

            print("user_id =>", user_id)

            if user_id is None:
                pass
            else:
                conn = MySQLdb.connect(self.db_host, self.db_user, self.db_passwd, self.db_name)
                with conn:
                    cursor = conn.cursor()

                    query_string = "SELECT * FROM records WHERE user_id = '{userid}'".format(userid=user_id) 
                    cursor.execute(query_string)
                    conn.commit()

                    dataset = cursor.fetchall()
                    print('Total Row(s) fetched:', cursor.rowcount)

                    result=[]

                    for row in dataset:
                        record_id = row[0]
                        task_id = row[1]
                        user_id = row[2]
                        result.append(task_id)

                        print ("record_id=%s,task_id=%s,user_id=%d" % (record_id, task_id, user_id))

                    j_res = json.dumps(result)              
                    gc.collect()

                    response_data = {
                            "msg": 'Success',
                            "ret": HTTP_202_ACCEPTED,
                            "data": {
                                "task_id_list": j_res,
                                }
                            }
                    response_json = make_response(jsonify(response_data), HTTP_202_ACCEPTED)
                    response_json.headers['Access-Control-Allow-Origin'] = '*'
                    return response_json
                    


        except Exception as e:
            return {'error': str(e)}
    
