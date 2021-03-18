from konlpy.tag import Hannanum
from konlpy.tag import Kkma
from krwordrank.hangle import normalize
from collections import Counter
from dotenv import load_dotenv
import re
import cx_Oracle
import os
import pytagcloud
import webbrowser


hannanum = Hannanum()
kkma = Kkma()

#hannanum.analyze()  # 구(Phrase) 분석
#hannanum.morphs()  # 형태소 분석
#hannanum.nouns()  # 명사 분석
#hannanum.pos()  # 형태소 분석 태깅

#kkma.morphs()  # 형태소 분석
#kkma.nouns()  # 명사 분석
#kkma.pos()  # 형태소 분석 태깅
#kkma.sentences()  # 문장 분석

load_dotenv()

def makeImage(wc):
    counter = Counter(wc)
    top100 = counter.most_common(100)

    # tag에 color, size, tag 사전 구성
    # maxsize : 최대 글자크기
    word_count_list = pytagcloud.make_tags(top100, maxsize=80)

    pytagcloud.create_tag_image(word_count_list,
                                'wordcloud.jpg',  # 생성될 시각화 파일 이름
                                size=(800, 600),  # 사이즈
                                fontname='korean',  # 한글 시각화를 위해 새로 추가했던 폰트 이름
                                rectangular=False)
    webbrowser.open('wordcloud.jpg')  # 저장된 'wordcloud.jpg' 브라우저로 띄워서 보기

os.putenv('NLS_LANG', '.UTF8')

def getBBSContent():
    dbInfo = os.getenv('DB_CON')
    conn = cx_Oracle.connect(dbInfo)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM(
        SELECT z.CONSSHOW_TYPE_CD,z.title, z.content, z.bbs_num
        FROM PUU_BBS_TB Z, PUU_BBS_MASTER_TB Y
         WHERE
             Z.DEL_YN='N'
             and Y.BBS_STATUS_CD='002'
             and Z.BBS_ID=Y.BBS_ID
             and Z.REPLY_LEVEL = '0'
             AND z.reg_dt >= to_date(2018,'yyyy')
             --AND z.consshow_type_cd IS NOT NULL
             AND z.content IS NOT NULL
             AND y.bbs_id not in (7, 103, 104, 120)
             and z.consshow_type_cd = 'O'
        ORDER BY z.reg_dt DESC
        )
        --where ROWNUM < 10
    """)

    res = cursor.fetchall()
    return res


def main():
    dbList = getBBSContent()
    bbs_list = []
    print("***********************************************************************************")
    for row in dbList:
        ret = re.sub('<.+?>', '', ''.join(row[2].read()), 0).strip().replace("\r\n", "")

        # if row[1] is not None:
        #     print("No." + str(row[3]) + " Title : " + row[1])
        for sent in kkma.sentences(ret):
            # if '문제' in sent:
            #     print(sent)
            # elif '분쟁' in sent:
            #     print(sent)
            # elif '관리' in sent:
            #     print(sent)
            # elif '서비스' in sent:
            #     print(sent)
            for (text, tclass) in kkma.pos(sent):
                if tclass == 'NNG' or tclass == 'NNP' or tclass == 'NP':
                    if len(str(text)) >= 2 and not (re.match('^[0-9]', text)):
                        bbs_list.append(normalize(text, english=True, number=True))

            bbs_list.append(sent)
            for noun in hannanum.morphs(sent):
                if len(str(noun)) > 3 and not (re.match('^[0-9]', noun)):
                    bbs_list.append(normalize(noun, english=True, number=True))
    word_count = {}
    for noun in bbs_list:
        word_count[noun] = word_count.get(noun, 0) + 1

    print("***********************************************************************************")

    for key, val in sorted(word_count.items(), key=lambda item: item[1], reverse=True):
        print("key = {key}, value={value}".format(key=key, value=val))

    # makeImage(word_count)


if __name__ == "__main__":
    main()