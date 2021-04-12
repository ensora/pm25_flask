from flask import Flask, Markup, render_template, redirect, jsonify, request, abort, url_for
from collections import defaultdict
import datetime
import json
import os
import maya
import requests
import operator
import logging
import random

app = Flask(__name__)


pm25_filename = os.path.join(app.static_folder, 'data', 'pm25_measurements.json')

pm25_measurements = []


def init_measurements(filename, measurements):
    with open(filename) as test_file:
        data = json.load(test_file)
        for p in data:
            measurements.append(p)
        test_file.close()

def write_measurements(my_measurements, filename):
    with open(filename, 'w') as outfile:
        outfile.write(json.dumps(my_measurements))
        outfile.close()

def get_time_to_dashboard(timestamp):
    d = datetime.datetime.today()
    d = maya.parse(d).datetime()
    mytime = int(d.strftime("%s"))
    dstr = d.strftime('%d-%m-%yT%H:%M:%S.%fZ')
    dt = convert_time(timestamp)
    servertime = int(dt.strftime("%s"))
    time_to_server = mytime - servertime
    time_obj = {
        "id": light_measurements[-1]["id"] + 1,
        "server_time" : timestamp,
        "dashboard_time" : dstr,
        "time_dif" : time_to_server
    }
    time_values.append(time_obj)
    write_measurements(time_values, time_file)



def convert_time(timestamp):
    dt = maya.parse(timestamp).datetime()
    return dt


def get_todays_values(data_set):
    todays_values=[]
    d = datetime.datetime.today()
    d = maya.parse(d).datetime()
    for item in data_set:
        time = convert_time(item.get('time'))
        if time.date() == d.date():
            todays_values.append(item)
    return todays_values

def sort_for_table(data_set):
    values_sorted=[]
    today_values = get_todays_values(data_set)
    for x in today_values:
        if x not in values_sorted:
            values_sorted.append(x)
    #values_sorted.sort(reverse=True)
    #app.logger.info(values_sorted)
    return values_sorted


def sort_by_hour(values_unsorted, keyvalue):
    values_sorted=[]
    for item in values_unsorted:
        time = convert_time(item.get('time'))
        if time.hour == keyvalue:
            values_sorted.append(item)
    return values_sorted


def sort_by_value(values_unsorted, keyname, keyvalue):
    values_sorted=[]
    for item in values_unsorted:
        if item.get(keyname) == keyvalue:
            values_sorted.append(item)
    return values_sorted


def split_data_time(data_set, timelabels):
    data_amt = []
    for item in timelabels:
        count = 0
        set = sort_by_hour(data_set, item)
        for i in set:
            count = count + 1
        data_amt.append(count)
    return data_amt


def sum_values(data_set, timelabels):
    data_summed = []
    for item in timelabels:
        count = 0
        set = sort_by_hour(data_set, item)
        for i in set:
            count = count + i['light_intensity']
        data_summed.append(count)
    return data_summed


def create_dataset(data_set, keyname, keyvalue, timelables):
    data_set = get_todays_values(data_set)
    sorted_set = sort_by_value(data_set, keyname, keyvalue)
    value_set = split_data_time(sorted_set, timelables)
    return value_set

def create_summed_dataset(data_set, timelables):
    data_set = get_todays_values(data_set)
    value_set = sum_values(data_set, timelables)
    return value_set


def create_timelables(data_set):
    labels = []
    cleanlabels = []
    data_set = get_todays_values(data_set)
    for item in data_set:
        time = convert_time(item['time'])
        time_string = time.hour
        labels.append(time_string)
    for x in labels:
        if x not in cleanlabels:
            cleanlabels.append(x)
    app.logger.info(cleanlabels)
    return cleanlabels


def get_values(tagname, filename):
    my_values = []
    with open(filename) as value_file:
        data = json.load(value_file)
        data = get_todays_values(data)
        for p in data:
            if tagname == 'time':
                time = convert_time(p['time'])
                my_values.append(time.time())
            else:
               my_values.append(p[tagname])
    value_file.close()
    return my_values


@app.route('/')
def start():
    init_measurements(pm25_filename, pm25_measurements)
    app.logger.info(pm25_measurements)
    return render_template('main.html')


@app.route('/measurements/pm25', methods = ['GET', 'POST'])
def pm2_requests():
    if request.method == 'GET':
        return jsonify({'pm25_measurements': pm25_measurements})
    if request.method == 'POST':
        if not request.json or not 'pred' in request.json:
            abort(400)
        pm25_measurement = {
            "id": pm25_measurements[-1]["id"] + 1,
            "pm25": request.json["pm25"],
            "pred": request.json["pred"],
            "city": "Vienna",
            "device": "BLESense-CD60",
            "time": request.json["time"],
        }
        pm25_measurements.append(pm25_measurement)
        write_measurements(pm25_measurements, pm25_filename)
        return jsonify({"pm25_measurements": pm25_measurements}), 201

@app.route('/measurements/savepm', methods = ['POST'])
def save_requests():
    if request.method == 'POST':
        #if request.form.get("Name") != "pmdata":
            #abort(400)
        #data = request.form.get("pmdata")
        pm25_measurement = {
            "id": random.randint(2, 9999),
            "pm25": request.form.get("pmdata"),
            "pred": request.form.get("pred"),
            "city": "Vienna",
            "device": "BLESense-CD60",
            "time": request.form.get("time"),
        }
        pm25_measurements.append(pm25_measurement)
        write_measurements(pm25_measurements, pm25_filename)
        return jsonify({"pm25_measurements": pm25_measurements}), 201


if __name__ == '__main__':
    init_measurements(pm25_filename, pm25_measurements)
    app.logger.info(pm25_measurements)
    app.run(host='0.0.0.0', debug=True)
