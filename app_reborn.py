# coding=utf8

import sys
import re
import urllib
import threading
import configparser
import logging
import http.cookiejar
import csv
import bs4
import time
import os
import hashlib
import glob
import json

import PyQt5

import gui.MainWindow

spacial_char = '↑↓←→↖↙↗↘↕'

url_stock_code = 'http://quote.eastmoney.com/stocklist.html'
url_currency_acronyms = 'http://www.easy-forex.com/int/zh-hans/currencyacronyms/'

api_sinajs = 'http://hq.sinajs.cn/rn={}&list={}'

key_stock_code = '">(.*?)\((.*?)\)<'


def get_current_time():
    return str(int(time.time()))


class App:
    """

    """

    isRunning = {}
    isRunning['app'] = True

    timeout = 10

    cookie = http.cookiejar.CookieJar()
    handler = urllib.request.HTTPCookieProcessor(cookie)
    opener = urllib.request.build_opener(handler)

    def __init__(self):

        logging.basicConfig(filename='app.log', level=logging.DEBUG, filemode='w',
                            format='%(relativeCreated)d[%(levelname).4s][%(threadName)-.10s]%(message)s')

        self.gameData = {}

        self.firstRun()
        self.load_config()
        self.load_user()
        self.load_cache()
        self.show_gui()
        self.show_cache()
        self.fetch_data()

    def firstRun(self):
        if not os.path.isdir('log'):
            os.mkdir('log')
        if not os.path.isdir('tmp'):
            os.mkdir('tmp')
        if not os.path.isdir('save'):
            os.mkdir('save')
        if not os.path.isdir('data'):
            os.mkdir('data')
        if not os.path.isdir('gui'):
            os.mkdir('gui')
        if not os.path.isdir('ai'):
            os.mkdir('ai')
        for file in glob.glob('tmp/*'):
            os.remove(file)

    def load_config(self):
        pass

    def load_user(self):
        pass

    def load_cache(self):
        pass

    def show_gui(self):
        def show():
            app = PyQt5.QtWidgets.QApplication(sys.argv)
            main_window = PyQt5.QtWidgets.QMainWindow()
            self.ui = Main_Window()
            self.ui.setupUi(main_window)
            self.ui.init(self.gameData)
            main_window.show()
            sys.exit(app.exec_())

        t_gui = threading.Thread(target=show)
        t_gui.start()

    def show_cache(self):
        pass

    def fetch_data(self):
        # 根据游戏内容，综合当前网络速度与延迟，拟决定用10个线程处理以下任务：
        # 以下任务同时进行：
        def Star():
            """伴飞卫星"""
            self.isRunning['Star'] = True
            shStatus = ''
            szStatus = ''
            while self.isRunning['Star']:
                if 'stockCode_sh' in self.gameData:
                    self.shStatus = '正在获取信息：{:.2f}%'
                    if 'new_data_sh' in self.gameData:
                        rate = len(self.gameData['new_data_sh'].items()) / len(self.gameData['stockCode_sh'])
                        self.shStatus = self.shStatus.format(rate * 100)
                else:
                    self.shStatus = '正在获取代码'

                if 'stockCode_sz' in self.gameData:
                    self.szStatus = '正在获取信息：{:.2f}%'
                    if 'new_data_sz' in self.gameData:
                        rate = len(self.gameData['new_data_sz'].items()) / len(self.gameData['stockCode_sz'])
                        self.szStatus = self.szStatus.format(rate * 100)
                else:
                    self.szStatus = '正在获取代码'

                if 'ui' in dir(self):
                    self.ui.set_status_bar_text('上海：{}；深圳：{}。'.format(self.shStatus, self.szStatus))
                time.sleep(0.1)

        def fetchDaPanData():
            """查询大盘信息"""
            self.isRunning['fetchDaPanData'] = True
            while self.isRunning['fetchDaPanData']:
                try:
                    logging.info('正在获取查询大盘指数…')
                    logging.info('大盘指数获取完毕。')
                    self.isRunning['fetchDaPanData'] = False
                except:
                    pass

        def fetchStockCode():
            """查询股票代码"""
            self.isRunning['fetchStockCode'] = True
            while self.isRunning['fetchStockCode']:
                try:
                    logging.info('正在获取股票代码…')
                    # 构建请求
                    request = urllib.request.Request(url_stock_code)
                    # 获取响应
                    response = self.opener.open(request, timeout=self.timeout)
                    # 解码
                    stockList = response.read().decode('gbk')
                    soup = bs4.BeautifulSoup(stockList, 'lxml')
                    pattern = re.compile('">(.*?)\((.*?)\)<')
                    self.gameData['stockCode_sh'] = re.findall(pattern, str(soup.find_all('ul')[7]))
                    self.gameData['stockCode_sz'] = re.findall(pattern, str(soup.find_all('ul')[8]))
                    self.isRunning['fetchStockCode'] = False
                except Exception as e:
                    logging.debug('fetchStockCode崩溃')

        def fetchSHStock():
            """用已保存的股票代码查询上证综合股票当前信息"""
            self.isRunning['fetchSHStock'] = True
            if 'new_data_sh' not in self.gameData:
                self.gameData['new_data_sh'] = {}
            if 'data_sh' not in self.gameData:
                self.gameData['data_sh'] = {}
            if 'fail_sh' not in self.gameData:
                self.gameData['fail_sh'] = []
            while self.isRunning['fetchSHStock']:
                if 'stockCode_sh' not in self.gameData:
                    time.sleep(0.1)
                else:
                    try:
                        logging.info('正在获取上海股票信息…')
                        tmp = []
                        for each in self.gameData['new_data_sh'].items():
                            tmp.append(each[0])
                        remainList = []
                        for each in self.gameData['stockCode_sh']:
                            if each[0] not in tmp:
                                remainList.append(each)
                        for i, v in enumerate(remainList):
                            # 构建请求
                            request = urllib.request.Request(api_sinajs.format(get_current_time(), 'sh' + v[1]))
                            # 获取响应
                            response = self.opener.open(request, timeout=self.timeout)
                            # 解码
                            shStatusList = response.read().decode('gbk')
                            info = shStatusList.split('"')[1]
                            if info == '':
                                self.gameData['fail_sh'].append(v[0])
                            else:
                                tmp = info.split(',')
                                tmp[0] = tmp[0].replace(' ', '')
                                logging.debug(
                                    '已获取上海"%s"的股票行情。(%s/%s)' % (tmp[0], i, len(self.gameData['stockCode_sh'])))
                                self.gameData['new_data_sh'][tmp[0]] = tmp

                        tmp = []
                        for each in self.gameData['new_data_sh'].items():
                            tmp.append(each[0])
                        remain = []
                        for each in self.gameData['stockCode_sh']:
                            if each[0] not in tmp:
                                remain.append(each[0])
                        text = '上海股票行情获取完毕。总数{}支，已加载{}支，未加载{}支。'
                        text = text.format(len(self.gameData['stockCode_sh']),
                                           len(self.gameData['new_data_sh'].items()),
                                           len(remain))
                        logging.info(text)
                        self.gameData['data_sh'] = self.gameData['new_data_sh']
                        self.isRunning['fetchSHStock'] = False

                    except urllib.error.URLError as e:
                        print(str(e))
                        logging.debug('fetchSHStock崩溃')
                        logging.error(str(e))
                        time.sleep(0.1)

        def fetchSZStock():
            """用已保存的股票代码查询深证成份股票当前信息"""
            self.isRunning['fetchSZStock'] = True
            if 'new_data_sz' not in self.gameData:
                self.gameData['new_data_sz'] = {}
            if 'data_sz' not in self.gameData:
                self.gameData['data_sz'] = {}
            if 'fail_sz' not in self.gameData:
                self.gameData['fail_sz'] = []
            while self.isRunning['fetchSZStock']:
                if 'stockCode_sz' not in self.gameData:
                    time.sleep(0.1)
                else:
                    try:
                        logging.info('正在获取深圳股票信息…')
                        tmp = []
                        for each in self.gameData['new_data_sz'].items():
                            tmp.append(each[0])
                        remainList = []
                        for each in self.gameData['stockCode_sz']:
                            if each[0] not in tmp:
                                remainList.append(each)
                        ###
                        newList = []
                        for each in remainList:
                            newList.append('sz' + each[1])
                        self.api_get_sinajs(get_current_time(), newList)
                        ###
                        for i, v in enumerate(remainList):
                            # 构建请求
                            request = urllib.request.Request(api_sinajs.format(get_current_time(), 'sz' + v[1]))
                            # 获取响应
                            response = self.opener.open(request, timeout=self.timeout)
                            # 解码
                            szStatusList = response.read().decode('gbk')
                            info = szStatusList.split('"')[1]
                            if info == '':
                                self.gameData['fail_sz'].append(v[0])
                            else:
                                tmp = info.split(',')
                                tmp[0] = tmp[0].replace(' ', '')
                                logging.debug(
                                    '已获取深圳"%s"的股票行情。(%s/%s)' % (tmp[0], i, len(self.gameData['stockCode_sz'])))
                                self.gameData['new_data_sz'][tmp[0]] = tmp

                        tmp = []
                        for each in self.gameData['new_data_sz'].items():
                            tmp.append(each[0])
                        remain = []
                        for each in self.gameData['stockCode_sz']:
                            if each[0] not in tmp:
                                remain.append(each[0])
                        text = '深圳股票行情获取完毕。总数{}支，已加载{}支，未加载{}支。'
                        text = text.format(len(self.gameData['stockCode_sz']),
                                           len(self.gameData['new_data_sz'].items()),
                                           len(remain))
                        logging.info(text)
                        self.gameData['data_sz'] = self.gameData['new_data_sz']
                        self.isRunning['fetchSZStock'] = False
                    except urllib.error.URLError as e:
                        print(str(e))
                        logging.debug('fetchSZStock崩溃')
                        logging.error(str(e))
                        time.sleep(0.1)

        star = threading.Thread(target=Star)
        dapan = threading.Thread(target=fetchDaPanData)
        stockCode = threading.Thread(target=fetchStockCode)
        shStock = threading.Thread(target=fetchSHStock)
        szStock = threading.Thread(target=fetchSZStock)
        star.start()
        dapan.start()
        stockCode.start()
        shStock.start()
        szStock.start()

    def api_get_sinajs(self, time, codeList):
        """
        :param time:int
        :param codeList:string_list
        :return info_dict:list_dict
        """
        retry_time = 3
        num_of_each_ask = 10
        ask_times = int(len(codeList) / num_of_each_ask) + 1
        # 把请求进行组合
        request_code_dict = {}
        for i in range(ask_times):
            request_code_dict[','.join(codeList[i * num_of_each_ask:i * num_of_each_ask + num_of_each_ask])] = False
        # 生成代码与回复对应的字典
        code_raw_dict = {}
        retry = True
        while retry:
            for each in request_code_dict.keys():
                # 构建请求
                request = urllib.request.Request(api_sinajs.format(time, each))
                # 获取响应
                response = self.opener.open(request, timeout=self.timeout)
                # 解码
                try:
                    raw_respond = response.read().decode('gbk')
                except urllib.error.URLError as e:
                    pass
                else:
                    respond_string_list = raw_respond.split('\n')
                    for i, every in enumerate(respond_string_list):
                        if every != '':
                            code_raw_dict[each.split(',')[i]] = every
                        else:
                            pass
                    request_code_dict[each] = True
                finally:
                    retry = False
                    for every in request_code_dict.keys():
                        if not request_code_dict[every]:
                            retry = True
        # 生成列表
        code_info_dict = {}
        for each in code_raw_dict.keys():
            value = code_raw_dict[each].split('"')[1]
            if value == '':
                pass
            elif value == 'FAILED':
                pass
            else:
                info = value.split(',')
                info[0] = info[0].replace(' ', '')
                info[0] = info[0].replace('　', '')
                code_info_dict[each]=info
        print(code_info_dict)
        return code_info_dict

        info_list = []
        null_list = []
        fail_list = []
        for i, each in enumerate(code_raw_dict.keys()):
            info_string = line.split('"')[1]
            if info_string == '':
                null_list.append(codeList[i])
                text = 'api返回Null。{}■{}'
                text = text.format(codeList[i], line)
                logging.debug(text)
            elif info_string == 'FAILED':
                fail_list.append(codeList[i])
                text = 'api返回FAILED。{}■{}'
                text = text.format(codeList[i], line)
                logging.debug(text)
            else:
                info = info_string.split(',')
                info[0] = info[0].replace(' ', '')
                info[0] = info[0].replace('　', '')
                info_list.append(info)
        info_dict = {}
        info_dict['info_list'] = info_list
        info_dict['null_list'] = null_list
        info_dict['fail_list'] = fail_list
        return info_dict


class Main_Window(PyQt5.QtWidgets.QMainWindow, gui.MainWindow.Ui_MainWindow):
    change_status_text = PyQt5.QtCore.pyqtSignal(str)
    add_list_widget_sh_item = PyQt5.QtCore.pyqtSignal(str)
    add_list_widget_sz_item = PyQt5.QtCore.pyqtSignal(str)

    def init(self, gameData):
        self.gameData = gameData
        self.change_status_text.connect(self._set_status_bar_text)
        self.add_list_widget_sh_item.connect(self._add_list_widget_sh)
        self.add_list_widget_sz_item.connect(self._add_list_widget_sz)
        self.listWidget_sh.itemClicked.connect(self._list_widget_sh_item_clicked)

    def set_status_bar_text(self, text):
        self.change_status_text.emit(text)

    def _set_status_bar_text(self, text):
        self.statusbar.showMessage(text)

    def add_list_widget_sh(self, text):
        self.add_list_widget_sh_item.emit(text)

    def _add_list_widget_sh(self, text):
        item = PyQt5.QtWidgets.QListWidgetItem()
        item.setText(text)
        self.listWidget_sh.addItem(item)

    def add_list_widget_sz(self, text):
        self.add_list_widget_sz_item.emit(text)

    def _add_list_widget_sz(self, text):
        item = PyQt5.QtWidgets.QListWidgetItem()
        item.setText(text)
        self.listWidget_sz.addItem(item)

    def _list_widget_sh_item_clicked(self, item):
        print(item.text())
        for each in self.gameData['new_data_sh'].keys():
            if self.gameData['new_data_sh'][each][0] == item.text():
                newList = self.gameData['new_data_sh'][each]
                newList[0] = '名称：' + newList[0]
                newList[1] = '今开：' + newList[1]
                newList[2] = '昨收：' + newList[2]
                newList[3] = '当前：' + newList[3]
                newList[4] = '最高：' + newList[4]
                newList[5] = '最低：' + newList[5]
                tmp = '\n'.join(newList[:6])
                self.label_sh.setText(tmp)
                break


if __name__ == '__main__':
    I = App()
