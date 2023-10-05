import random
from time import time, localtime
import cityinfo
from requests import get, post
from datetime import datetime, date
import sys
import os
import http.client, urllib
from zhdate import ZhDate
import json
from warnings import warn


class DailyLovePush:
    def __init__(self, cfg_path="./config.json"):
        self.cfg_path = cfg_path
        self.config = {}
        self.week_list = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"]

        self.jieqi_info = {
            "month_jieqi": {
            1: ["小寒","大寒"], 2: ["立春","雨水"], 3: ["惊蛰",'春分'], 4: ["清明","谷雨"],
            5: ["立夏","小满"], 6: ["芒种","夏至"], 7: ["小暑","大暑"], 8: ["立秋","处暑"],
            9: ["白露","秋分"], 10: ["寒露","霜降"], 11: ["立冬","小雪"], 12: ['大雪',"冬至"]
        },
            "is_today" : False,
            "jieqi_poem": "",
            "curr_jieqi": ""
        }
        self.date_info = {}
        self.out_data = {}
        self.out_data_content = {}
        self.init_file()

    def init_file(self):
        with open(self.cfg_path, encoding="utf-8") as f:
            self.config = json.load(f)
        year = localtime().tm_year
        month = localtime().tm_mon
        day = localtime().tm_mday
        today = datetime.date(datetime(year=year, month=month, day=day))
        week = self.week_list[today.isoweekday() % 7]
        self.date_info = {
            'year': year, 'month': month, 'day': day,
            'today': today, 'week': week,
        }

    def get_color(self, obj):
        color_dict = {
            "date": "#238E23",
            "city": "#3F3E3F",
            "weather": "#5B8982",
            "min_temperature": "#007FFF",
            "max_temperature": "#FF2400",
            "love_day": "#FF7F00",
            "birthday1": "#F5D040",
            "birthday2": "#F5D040",
            "note_en": "#38B0DE",
            "lucky": "#F5D040",
            "poem": "#FF2400",
            "daily_tip": "#f58c71",
            "silly_love_sentence": "#6f97df",
            "air_quality": "#000000",
            "others": "#6B8E34"
        }
        if obj not in color_dict:
            return self.gen_random_color()
        else:
            return color_dict.get(obj)

    @staticmethod
    def gen_random_color():
        # 获取随机颜色
        get_colors = lambda n: list(map(lambda i: "#" + "%06x" % random.randint(0, 0xFFFFFF), range(n)))
        color_list = get_colors(100)
        return random.choice(color_list)

    def cntdwn_birthday(self, birthday):
        year = self.date_info.get('year')
        today = self.date_info.get('today')
        birthday_year = birthday.split("-")[0]
        # 判断是否为农历生日
        if birthday_year[0] == "r":
            r_mouth = int(birthday.split("-")[1])
            r_day = int(birthday.split("-")[2])
            # 今年生日
            birthday = ZhDate(year, r_mouth, r_day).to_datetime().date()
            year_date = birthday

        else:
            # 获取国历生日的今年对应月和日
            birthday_month = int(birthday.split("-")[1])
            birthday_day = int(birthday.split("-")[2])
            # 今年生日
            year_date = date(year, birthday_month, birthday_day)
        # 计算生日年份，如果还没过，按当年减，如果过了需要+1
        if today > year_date:
            if birthday_year[0] == "r":
                # 获取农历明年生日的月和日
                r_last_birthday = ZhDate((year + 1), r_mouth, r_day).to_datetime().date()
                birth_date = date((year + 1), r_last_birthday.month, r_last_birthday.day)
            else:
                birth_date = date((year + 1), birthday_month, birthday_day)
            birth_day = str(birth_date.__sub__(today)).split(" ")[0]
        elif today == year_date:
            birth_day = 0
        else:
            birth_date = year_date
            birth_day = str(birth_date.__sub__(today)).split(" ")[0]
        return birth_day

    def get_weather(self):
        # 城市id
        province, city = self.config["province"], self.config["city"]
        try:
            city_id = cityinfo.cityInfo[province][city]["AREAID"]
        except KeyError:
            print("推送消息失败，请检查省份或城市是否正确")
            os.system("pause")
            sys.exit(1)
        # city_id = 101280101
        # 毫秒级时间戳
        t = (int(round(time() * 1000)))
        headers = {
            "Referer": "http://www.weather.com.cn/weather1d/{}.shtml".format(city_id),
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
        }
        url = "http://d1.weather.com.cn/dingzhi/{}.html?_={}".format(city_id, t)
        response = get(url, headers=headers)
        response.encoding = "utf-8"
        response_data = response.text.split(";")[0].split("=")[-1]
        response_json = eval(response_data)
        weatherinfo = response_json["weatherinfo"]
        self.out_data_content["weather"] = {
            "value": weatherinfo["weather"],
            "color": self.get_color("weather")
        }
        self.out_data_content["temperature_range"] = {
            "value": weatherinfo["tempn"] + "°C ~ " + weatherinfo["temp"],
            "color": self.get_color("max_temperature")
        }

    def get_weather_tmp(self):
        # 城市id
        province = '湖北'
        city = '宜昌'
        self.out_data_content['city_tmp'] = {
            "value": city,
            "color": self.get_color('city')
        }
        try:
            city_id = cityinfo.cityInfo[province][city]["AREAID"]
        except KeyError:
            print("推送消息失败，请检查省份或城市是否正确")
            os.system("pause")
            sys.exit(1)
        # 毫秒级时间戳
        t = (int(round(time() * 1000)))
        headers = {
            "Referer": "http://www.weather.com.cn/weather1d/{}.shtml".format(city_id),
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
        }
        url = "http://d1.weather.com.cn/dingzhi/{}.html?_={}".format(city_id, t)
        response = get(url, headers=headers)
        response.encoding = "utf-8"
        response_data = response.text.split(";")[0].split("=")[-1]
        response_json = eval(response_data)
        weatherinfo = response_json["weatherinfo"]
        self.out_data_content["weather_tmp"] = {
            "value": weatherinfo["weather"],
            "color": self.get_color("weather")
        }
        self.out_data_content["temperature_range_tmp"] = {
            "value": weatherinfo["tempn"] + "°C ~ " + weatherinfo["temp"],
            "color": self.get_color("max_temperature")
        }

    def get_jieqi(self):

        import time
        self.jieqi_info["jieqi_poem"] = ""
        conn = http.client.HTTPSConnection('apis.tianapi.com')  # 接口域名
        headers = {'Content-type': 'application/x-www-form-urlencoded'}
        jieqi_list = []
        for m, j_list in self.jieqi_info["month_jieqi"].items():
            if self.date_info['month'] -1 <= m <= self.date_info['month'] + 1:
                jieqi_list.extend(j_list)

        for j in jieqi_list:
            params = urllib.parse.urlencode({'key': self.config["tianxing_API"], 'word': j, 'year': self.date_info['year']})
            conn.request('POST', '/jieqi/index', params, headers)
            tianapi = conn.getresponse()
            result = tianapi.read()
            data = result.decode('utf-8')
            dict_data = json.loads(data)
            start_date = dict_data['result']['date']['gregdate'].split("-")[1:]
            self.jieqi_info["jieqi_poem"] = dict_data['result']['shiju']
            start_date_cnt = int(start_date[0]) * 100 + int(start_date[1])
            curr_date_cnt = self.date_info.get('month')*100 + self.date_info.get('day')
            if start_date_cnt <= curr_date_cnt:
                self.jieqi_info["curr_jieqi"] = "正值" + j
                time.sleep(0.1)
                continue
            else:
                if start_date_cnt == curr_date_cnt:
                    self.jieqi_info["is_today"] = True
                break
        self.jieqi_info["is_today"] = True
        if not self.jieqi_info["is_today"]:
            self.out_data_content['date']['value'] += "，" + self.jieqi_info["curr_jieqi"]

    # 词霸每日一句
    def get_ciba(self):
        if self.config["Whether_Eng"]:
            try:
                url = "http://open.iciba.com/dsapi/"
                headers = {
                    'Content-Type': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                  'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
                }
                r = get(url, headers=headers)
                self.out_data_content["note_en"] = {
                    "value": r.json()["content"],
                    "color": self.get_color("note_en")
                }
                self.out_data_content["note_ch"] = {
                    "value": r.json()["note"],
                    "color": self.get_color("note_ch")
                }
            except Exception as ex:
                warn("词霸API调取错误: %s" % ex)

    def caihongpi(self):
        if self.config["Whether_caihongpi"]:
            try:
                conn = http.client.HTTPSConnection('api.tianapi.com')  # 接口域名
                params = urllib.parse.urlencode({'key': self.config["tianxing_API"]})
                headers = {'Content-type': 'application/x-www-form-urlencoded'}
                conn.request('POST', '/caihongpi/index', params, headers)
                res = conn.getresponse()
                data = res.read()
                data = json.loads(data)
                pipi = data["newslist"][0]["content"]
                if ("XXX" in data):
                    data.replace("XXX", "蒋蒋")
                self.out_data_content["pipi"] = {
                    "value": pipi,
                    "color": self.get_color("pipi")
                }
            except Exception as ex:
                warn("彩虹屁API调取错误，请检查API是否正确申请或是否填写正确: %s" % ex)

    # 健康小提示API
    def get_health(self):
        if self.config["Whether_health"]:
            try:
                conn = http.client.HTTPSConnection('api.tianapi.com')  # 接口域名
                params = urllib.parse.urlencode({'key': self.config["tianxing_API"]})
                headers = {'Content-type': 'application/x-www-form-urlencoded'}
                conn.request('POST', '/healthtip/index', params, headers)
                res = conn.getresponse()
                data = res.read()
                data = json.loads(data)
                self.out_data_content["health_tip"] = {
                    "value": data["newslist"][0]["content"],
                    "color": self.get_color("health_tip")
                }
            except Exception as ex:
                warn("健康小提示API调取错误，请检查API是否正确申请或是否填写正确: %s" % ex)

    # 星座运势
    def lucky(self):
        # TODO:变量名规范化
        if self.config["Whether_lucky"]:
            try:
                conn = http.client.HTTPSConnection('api.tianapi.com')  # 接口域名
                params = urllib.parse.urlencode({'key': self.config["tianxing_API"],
                                                 'astro': self.config["astro"].lower()})
                headers = {'Content-type': 'application/x-www-form-urlencoded'}
                conn.request('POST', '/star/index', params, headers)
                res = conn.getresponse()
                data = res.read()
                data = json.loads(data)
                lucky_str = str(data["newslist"][8]["content"])
                lucky_ = lucky_str.split('，')[0] + '~'
                self.out_data_content["lucky"] = {
                    "value": lucky_,
                    "color": self.get_color("lucky")
                }
            except Exception as ex:
                warn("星座运势API调取错误，请检查API是否正确申请或是否填写正确 %s" % ex)

    # 励志名言
    def lizhi(self):
        if self.config["Whether_lizhi"]:
            try:
                conn = http.client.HTTPSConnection('api.tianapi.com')  # 接口域名
                params = urllib.parse.urlencode({'key': self.config["tianxing_API"]})
                headers = {'Content-type': 'application/x-www-form-urlencoded'}
                conn.request('POST', '/lzmy/index', params, headers)
                res = conn.getresponse()
                data = res.read()
                data = json.loads(data)
                self.out_data_content["lizhi"] = {
                    "value":  data["newslist"][0]["saying"],
                    "color": self.get_color("lizhi")
                }
            except Exception as ex:
                warn("励志古言API调取错误，请检查API是否正确申请或是否填写正确: %s" % ex)

    def get_poem(self):
        if self.jieqi_info["is_today"]:
            self.out_data_content["poem"] = {
                "value": self.jieqi_info["curr_jieqi"] + ": " + self.jieqi_info["jieqi_poem"],
                "color": self.get_color("weather")
            }
            return

        try:
            conn = http.client.HTTPSConnection('apis.tianapi.com')  # 接口域名
            params = urllib.parse.urlencode({'key': self.config["tianxing_API"]})
            headers = {'Content-type': 'application/x-www-form-urlencoded'}
            conn.request('POST', '/duishici/index', params, headers)
            tianapi = conn.getresponse()
            result = tianapi.read()
            data = result.decode('utf-8')
            dict_data = json.loads(data)
            quest = "问答环节：" +  dict_data['result']['quest'] + "，？"
            self.out_data_content["poem"] = {
                "value": quest,
                "color": self.get_color("weather")
            }
        except Exception as ex:
            warn(ex)

    # 下雨概率和建议
    def tip(self):
        pop, tips = "", ""
        if not self.config["Whether_tip"]:
            return
        try:
            conn = http.client.HTTPSConnection('api.tianapi.com')  # 接口域名
            params = urllib.parse.urlencode({'key': self.config["tianxing_API"],
                                             'city': self.config["city"]})
            headers = {'Content-type': 'application/x-www-form-urlencoded'}
            conn.request('POST', '/tianqi/index', params, headers)
            res = conn.getresponse()
            data = res.read()
            data = json.loads(data)
            tips = data["newslist"][0]["tips"]

            self.out_data_content["tips"] = {
                "value": tips,
                "color": self.get_color("tips")
            }
        except Exception as ex:
            warn(f"天气预报API调取错误: {ex}")
            return pop, tips

    def get_silly_love_sentence(self):
        out = ""
        if not self.config.get('get_silly_love_sentence', False):
            return out
        try:
            conn = http.client.HTTPSConnection('apis.tianapi.com')  # 接口域名
            params = urllib.parse.urlencode({'key': self.config["tianxing_API"]})
            headers = {'Content-type': 'application/x-www-form-urlencoded'}
            conn.request('POST', '/saylove/index', params, headers)
            tianapi = conn.getresponse()
            result = tianapi.read()
            data = result.decode('utf-8')
            dict_data = json.loads(data)
            res = dict_data['result']
            out = res['content'].replace("\r\n", ",").replace('\n', ',')
            self.out_data_content["silly_love_sentence"] = {
                "value": out,
                "color": self.get_color("silly_love_sentence")
            }
        except Exception as ex:
            warn(f"土味情话API调取错误: {ex}")
            return out

    def get_movie_line(self):
        out = ""
        if not self.config.get('get_movie_line', False):
            return out
        try:
            conn = http.client.HTTPSConnection('apis.tianapi.com')  # 接口域名
            params = urllib.parse.urlencode({'key': self.config["tianxing_API"]})
            headers = {'Content-type': 'application/x-www-form-urlencoded'}
            conn.request('POST', '/dialogue/index', params, headers)
            tianapi = conn.getresponse()
            result = tianapi.read()
            data = result.decode('utf-8')
            dict_data = json.loads(data)
            res = dict_data['result']
            out = f"经典台词: "
            if len(res['english']) > 0:
                out += res['english']
            else:
                out += res['dialogue']
            out += " ——《%s》" % res['source']
            self.out_data_content["movie_line"] = {
                "value": out,
                "color": self.get_color("movie_line")
            }
        except Exception as ex:
            warn(f"经典台词API调取错误: {ex}")
            return out

    def get_daily_tip(self):
        out = ""
        if not self.config.get('get_daily_tip', False):
            return out
        try:
            conn = http.client.HTTPSConnection('apis.tianapi.com')  # 接口域名
            params = urllib.parse.urlencode({'key': self.config["tianxing_API"]})
            headers = {'Content-type': 'application/x-www-form-urlencoded'}
            conn.request('POST', '/qiaomen/index', params, headers)
            tianapi = conn.getresponse()
            result = tianapi.read()
            data = result.decode('utf-8')
            dict_data = json.loads(data)
            res = dict_data['result']
            out = "生活tip: %s" % res['content']
            self.out_data_content["daily_tip"] = {
                "value": out,
                "color": self.get_color("daily_tip")
            }
        except Exception as ex:
            warn(f"生活小窍门API调取错误: {ex}")
            return out

    def get_air_quality(self):
        out = ""
        if not self.config.get('get_air_quality', False):
            return out
        try:
            conn = http.client.HTTPSConnection('apis.tianapi.com')  # 接口域名
            params = urllib.parse.urlencode({'key': self.config["tianxing_API"], 'area': self.config["city"]})
            headers = {'Content-type': 'application/x-www-form-urlencoded'}
            conn.request('POST', '/aqi/index', params, headers)
            tianapi = conn.getresponse()
            result = tianapi.read()
            data = result.decode('utf-8')
            dict_data = json.loads(data)
            res = dict_data['result']
            # out = f"空气{res['quality']}, pm2.5={res['pm2_5']}"
            out = f"空气{res['quality']}"
            self.out_data_content["air_quality"] = {
                "value": out,
                "color": self.get_color("air_quality")
            }
        except Exception as ex:
            warn(f"空气质量API调取错误: {ex}")
            return out

    def get_air_quality_tmp(self):
        # 城市id
        city = '宜昌'
        out = ""
        if not self.config.get('get_air_quality', False):
            return out
        try:
            conn = http.client.HTTPSConnection('apis.tianapi.com')  # 接口域名
            params = urllib.parse.urlencode({'key': self.config["tianxing_API"], 'area': city})
            headers = {'Content-type': 'application/x-www-form-urlencoded'}
            conn.request('POST', '/aqi/index', params, headers)
            tianapi = conn.getresponse()
            result = tianapi.read()
            data = result.decode('utf-8')
            dict_data = json.loads(data)
            res = dict_data['result']
            out = f"空气{res['quality']}"
            self.out_data_content["air_quality_tmp"] = {
                "value": out,
                "color": self.get_color("air_quality")
            }
        except Exception as ex:
            warn(f"空气质量API调取错误: {ex}")
            return out

    def create_data_per_user(self, user):
        return {
            "touser": user,
            "template_id": self.config["template_id"],
            "url": "http://weixin.qq.com/download",
            "topcolor": "#FF0000"
        }

    def get_basic_info(self):
        """获取星期数、城市名声等基础输入"""

        self.out_data_content['date'] = {
            "value": "{}-{} {}".format(
                self.date_info.get('month'),
                self.date_info.get('day'),
                self.date_info.get('week')),
            "color": self.get_color("date")
        }
        self.out_data_content['city'] = {
            "value": self.config["city"],
            "color": self.get_color("city")
        }

    # 推送信息
    def send_message(self):
        # TODO: data字典的组装要根据实际情况,自动跳过未正确获取的字段
        # exit(1)
        # 获取日期信息
        # 传入省份和市获取天气信息
        self.get_basic_info()
        self.get_jieqi()
        self.get_weather()
        self.get_weather_tmp()
        self.get_ciba()     # 获取词霸每日金句
        self.caihongpi()    # 彩虹屁
        self.get_health()  # 健康小提示
        self.tip()  # 下雨概率和建议
        self.lizhi()    # 励志名言
        self.lucky()   # 星座运势
        self.get_love_days()    # 恋爱纪念日
        self.get_birthdays()    # 获取所有生日数据
        self.get_poem()     # 诗词
        self.get_air_quality()
        self.get_air_quality_tmp()

        # self.get_movie_line()
        self.get_silly_love_sentence()
        # self.get_daily_tip()

        self.diy_sentence()
        self.out_data['data'] = self.out_data_content
        print(self.out_data_content)

    def diy_sentence(self):
        self.out_data_content["ps"] = {
            "value": " home sweet home :)",
            "color": self.get_color("others")
        }

    def get_birthdays(self):
        birthdays = {}
        for k, v in self.config.items():
            if k[0:5] == "birth":
                birthdays[k] = v
        for i, (key, value) in enumerate(birthdays.items()):
            # 获取距离下次生日的时间
            birth_day = self.cntdwn_birthday(value)
            # 将生日数据插入data
            self.out_data_content[key] = {
                "value": birth_day,
                "color": self.get_color(f'birthday{i + 1}')}

    def get_access_token(self):
        # appId
        app_id = self.config["app_id"]
        # appSecret
        app_secret = self.config["app_secret"]
        post_url = ("https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={}&secret={}"
                    .format(app_id, app_secret))
        try:
            access_token = get(post_url).json()['access_token']
        except KeyError:
            print("获取access_token失败，请检查app_id和app_secret是否正确")
            os.system("pause")
            sys.exit(1)
        return access_token

    def post_msg(self, access_token):

        url = "https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={}".format(access_token)
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
        }
        res = post(url, headers=headers, json=self.out_data)
        response = res.json()
        if response["errcode"] == 40037:
            print("推送消息失败，请检查模板id是否正确")
        elif response["errcode"] == 40036:
            print("推送消息失败，请检查模板id是否为空")
        elif response["errcode"] == 40003:
            print("推送消息失败，请检查微信号是否正确")
        elif response["errcode"] == 0:
            print("推送消息成功")
        else:
            print(response)

    def get_love_days(self):
        # 获取在一起的日子的日期格式
        love_year = int(self.config["love_date"].split("-")[0])
        love_month = int(self.config["love_date"].split("-")[1])
        love_day = int(self.config["love_date"].split("-")[2])
        love_date = date(love_year, love_month, love_day)
        # 获取在一起的日期差
        love_days = str(self.date_info.get('today').__sub__(love_date)).split(" ")[0]
        self.out_data_content["love_day"] = {
            "value": love_days,
            "color": self.get_color("love_day")
        }

    def start(self):
        # 获取accessToken
        access_token = self.get_access_token()
        # 接收的用户
        users = self.config["user"]
        # 公众号推送消息
        for user in users:
            self.out_data = self.create_data_per_user(user)
            self.send_message()
            self.post_msg(access_token)


if __name__ == "__main__":
    love_push = DailyLovePush()
    love_push.start()
