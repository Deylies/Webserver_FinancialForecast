import sqlite3
import os
import pandas as pd
abs_path = os.getcwd()


class DB_Connector():
    def __init__(self):
        # print(os.path.join(abs_path, 'db', 'mds_jinrong.db'))
        self.con = sqlite3.connect(os.path.join(abs_path, 'db', 'mds_jinrong.db'))
        self.curse = self.con.cursor()
        self.table = "mds_jinrong_day"

    def init_envsurvey(self):
        # 名称,大类,小类,时间,数据
        self.curse.execute("""
        create table if not exists mds_jinrong_day (
        name char(32) not null,
        class1 char(32) not null,
        class2 char(32) not null,
        date DATE not null,
        data float(32) not null,
        primary key(name,class1,class2,date)
        )
        """)

    def upload_csv(self, filepath):
        # csv_file = pd.read_csv(filepath, delimiter=',', dtype=str)
        status = True
        try:
            csv_file = pd.read_csv(filepath,delimiter=',',encoding='gbk',dtype=str)
        except UnicodeDecodeError:
            csv_file = pd.read_csv(filepath, delimiter=',', encoding='utf-8')
        except Exception as e:
            print(e)
            status = False
        if status:
            for index in csv_file.index:
                try:
                    self.curse.execute("insert into %s (name,class1,class2,date,data) values%s"%(self.table,str(tuple(map(str,csv_file.loc[index,:])))))
                except sqlite3.IntegrityError:
                    self.curse.execute("update "+self.table+ " set name='%s',class1='%s',class2='%s',date='%s',data='%s'"%tuple(map(str, csv_file.loc[index, :]))+
                                     " where name='%s' and class1='%s' and class2='%s' and date='%s'"%tuple(map(str, csv_file.loc[index, :]))[:-1])
                except Exception as e:
                    print(e)
                print(filepath,"done",list(csv_file.loc[index,:]))
            self.con.commit()

    def drop(self):
        self.curse.execute("drop table if exists mds_jinrong_day")

    def close(self):
        self.curse.close()
        self.con.close()


def download_all():
    db = DB_Connector()
    db.curse.execute("select * from mds_env_survey")
    data = db.curse.fetchall()
    dt = [i[1:-1] for i in data]
    pics = {i[-1]: i[3] for i in data if i[-1] and i[3]}
    all_cols_table = """业务人员,日期,企业名称,业主姓名,业主电话,业主职务,企业地址,经纬度,环评情况,报告书,报告表,登记表,现场相符,不否说明,验收情况,为什么没验收,生产工艺,原辅料,成品,危险品,重点污染,环境应急预案,清洁生产,污水,吨位,污水处理,废气,风量,废气处理,污泥,油漆,金属,粉尘,废弃物,其他物质说明,噪音,片碱,PAC,PAM,碳酸钙,除磷剂,哪里需要改造,注"""
    cols = all_cols_table.split(',')
    dt = [cols] + dt
    import xlwt, os, zipfile
    wbk = xlwt.Workbook()
    sheet = wbk.add_sheet('Sheet1', cell_overwrite_ok=True)
    for i in range(len(dt)):
        for j in range(len(dt[i])):
            sheet.write(i, j, dt[i][j])
    wbk.save('static/download_all/all.xls')
    for k, v in pics.items():
        if not os.path.exists(os.path.join(os.getcwd(), 'static', 'download_all', v)):
            os.mkdir(os.path.join(os.getcwd(), 'static', 'download_all', v))
        for pic in k.split(','):
            os.system("cp db/pics/%s static/download_all/%s/%s" % (pic, v, pic))
    startdir = os.path.join(os.getcwd(), 'static', 'download_all')
    file_news = os.path.join(os.getcwd(), 'static', 'download_all') + '.zip'
    z = zipfile.ZipFile(file_news, 'w', zipfile.ZIP_DEFLATED)
    for dirpath, dirnames, filenames in os.walk(startdir):
        fpath = dirpath.replace(startdir, '')
        fpath = fpath and fpath + os.sep or ''
        for filename in filenames:
            z.write(os.path.join(dirpath, filename), fpath + filename)
            print('压缩成功')
    z.close()
    os.system("rm -rf static/download_all/*")


# def read_word(f_name):
#     import docx
#     doc_file = docx.Document(f_name)
#     for i in range(len(doc_file.paragraphs)):
#         print("第" + str(i) + "段的内容是：" + doc_file.paragraphs[i].text)

if __name__ == '__main__':
    # read_word("requirment.docx")
    db = DB_Connector()
    db.curse.execute("delete from "+db.table)
    import os
    for ff in os.listdir('requirment'):
        db.upload_csv("requirment/%s"%ff)
    db.close()
    # db.curse.execute("select * from %s"%db.table)
    # for i in db.curse.fetchall():
    #     if i[1]=='大类':
    #         print(i)
    # db.drop()
    # db.init_envsurvey()
