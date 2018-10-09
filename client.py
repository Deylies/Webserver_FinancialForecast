from flask import Flask, render_template, jsonify,request,redirect,url_for
from db_client import DB_Connector
import os
import pandas as pd
import datetime

abs_path = os.getcwd()
app = Flask(__name__)
URL, PORT = '0.0.0.0',6007
def main(cls,name,msg,warn):
    db = DB_Connector()
    db.curse.execute("select class1 from mds_jinrong_day group by class1")
    dalei = [i[0] for i in db.curse.fetchall()]
    dalei.remove(cls)
    dalei = [cls]+dalei
    db.curse.execute("select name from %s where class1='%s' group by name" % (db.table,cls ))
    names = sorted([str(i[0]) for i in db.curse.fetchall()])
    names.remove(name)
    names = [name]+names
    db.curse.execute("select class2,date,data from %s where class1='%s' and name='%s'" % (db.table, cls, name))
    dt = pd.DataFrame(db.curse.fetchall(), columns=['class2', 'date', 'data'],dtype=str)
    lines = []
    legend = []
    xAxis = set()
    predict_data = []
    if cls=='银行':
        tb_header = "一万元投资预计年收益(元)"
        colnames = ['#', '预计收益']
    else:
        tb_header = "七日预测数据"
        colnames = ['#', '第1日','第2日','第3日','第4日','第5日','第6日','第7日']
    for cls2 in dt.groupby('class2'):
        time_serise = cls2[1]
        time_serise.loc[:, 'date'] = pd.to_datetime(time_serise['date'])
        time_serise.loc[time_serise[time_serise['data'] == 'nan'].index, ['data']] = 0
        time_serise.loc[:, 'data'] = pd.to_numeric(time_serise['data'])
        time_serise = time_serise.sort_values('date')
        time_serise.dropna()
        last_day = time_serise.loc[time_serise.index[-1], 'date']
        origin_data = [
            cls2[0],
            list(time_serise['date']),
            list(time_serise['data'])
        ]
        last = float(time_serise.loc[time_serise.index[-1]]['data'])
        mean = float(time_serise['data'].mean())
        predict = last*0.5+mean*0.5
        if cls=='银行':
            predict_data.append({'name': str(cls2[0]),
                                 'date': str(last_day).split(' ')[0],
                                 'data': [round(predict*100,2)]})
        else:
            step = (last-mean)/7
            predict = [round(i*step+last,2) for i in range(7)]
            predict_data.append({'name': str(cls2[0]),
                                 'date': str(last_day).split(' ')[0],
                                 'data': predict})
        legend.append(str(cls2[0]))
        for i in list(time_serise['date']):
            xAxis.add(i)
        xAxis.add(last_day)
        xAxis.add(datetime.timedelta(days=1) + last_day)
        lines.append(origin_data)
    xAxis = list(sorted(xAxis))
    new_lines = []
    for line in lines:
        tmp_data = [None for _ in range(len(xAxis))]
        for j in range(len(line[1])):
            tmp_data[xAxis.index(line[1][j])] = line[2][j]
        new_lines.append([line[0], [float(p) if p else 0. if p != None else None for p in tmp_data]])
    xAxis = [str(i).split(' ')[0] for i in xAxis]
    return render_template('home.html', lines=new_lines, dalei=dalei, names=names, char_name=name, legend=legend,
                           xAxis=xAxis, predict_data=predict_data,message=msg,warn=warn,tb_header=tb_header,colnames=colnames)


@app.route('/',methods=['POST','GET'])
def home():
    msg = request.args.get('msg')
    warn = request.args.get('warn')
    if request.method=='GET':
        db = DB_Connector()
        db.curse.execute("select class1,name from mds_jinrong_day limit 1")
        dt = db.curse.fetchone()
        print(dt)
        cls = dt[0]
        name = dt[1]
        return main(cls,name,msg,warn)
    elif request.method=='POST':
        cls = request.form.get('dalei')
        name = request.form.get('name')
        return main(cls,name,msg,warn)

@app.route('/name',methods=['POST'])
def name():
    cls = request.form.get('class1')
    db = DB_Connector()
    db.curse.execute("select name from %s where class1='%s' group by name"%(db.table,cls))
    names = sorted([str(i[0]) for i in db.curse.fetchall()])
    # print(names)
    return jsonify(names)

@app.route('/upload',methods=['POST'])
def upload():
    # print(request.files)
    csvs = request.files.getlist("file-multiple-input")
    try:
        db = DB_Connector()
        for csv in csvs:
            db.upload_csv(csv)
        return redirect(url_for('home',msg='上传成功'))
    except:
        return redirect(url_for('home', warn='请检查数据！'))

if __name__ == '__main__':
    app.run(URL,PORT)

