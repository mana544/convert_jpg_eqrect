# -*- coding: utf-8 -*-
import struct
import sys
import os
import re
import tkinter
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk
import json
import threading

'''
JPEGファイル内に全天球情報(APP1 Photo Sphere XMP)を埋め込む。
APP0(JFIF)もしくはAPP1(Exif)の直後に埋め込みます。
Exif以外のAPP1(xmp)セグメントが元々埋め込まれている場合は、
その情報は破棄します。

【動作環境(使用モジュール)】
Python(Anaconda) 3.6.4(5.1.0)
tkinter 8.6
'''


# ファイ選択ダイアログコールバック
def btn_fileopen_callback():
    # ファイル選択アクションが重たくて、いつまで経ってもreturnされないので、
    # アクション本体は別スレッドで実行
    th = threading.Thread(target=fileopen_action)
    th.start()

# ファイル選択
def fileopen_action():
    # ブランクウインドウ出現時の回避策
    # root = tkinter.Tk()
    # root.withdraw()
    fTyp = [("JPEG File","*.jpg")]
    iDir = os.path.abspath(os.path.dirname(__file__))
    jpgfilename = filedialog.askopenfilename(filetypes = fTyp,initialdir = iDir)
    txtVal_filename.set(jpgfilename)

# 「設定値保存」ボタンアクション
def btn_saveSetting_action():
        # 保存するjsonセクションと設定値dictを定義
        section="convert_jpg_eqrect"
        setting = {'txtVal_FullPanoWidthPixels': txtVal_FullPanoWidthPixels.get(),                       # String
                   'txtVal_FullPanoHeightPixels': txtVal_FullPanoHeightPixels.get(),                     # String
                   'txtVal_CroppedAreaImageWidthPixels': txtVal_CroppedAreaImageWidthPixels.get(),       # String
                   'txtVal_CroppedAreaImageHeightPixels': txtVal_CroppedAreaImageHeightPixels.get(),     # String
                   'txtVal_CroppedAreaLeftPixels': txtVal_CroppedAreaLeftPixels.get(),                   # String
                   'txtVal_CroppedAreaTopPixels': txtVal_CroppedAreaTopPixels.get(),
                   'txtVal_filename': txtVal_filename.get()}                     # String
        saveSetting(section, setting)
        print("設定値を保存しました。")
        messagebox.showinfo('設定値保存','設定値を保存しました。')

# JSON保存
def saveSetting(section, setting):
    '''
    設定ファイル(setting.json)に内容を保存する。
    
    Parameters
    ----------
    section : str
        何のセクションを読み取るか？
        全天球イラストJPEGメタデータ埋め込み : 'convert_jpg_eqrect'

    setting : dict
        設定情報。
        キーや内容はセクションによって異なります。

    Returns
    -------
    None
    '''
    with open('setting.json','r',encoding='utf-8') as f:
        json_setting = json.loads(f.read())

    json_setting[section] = setting
    text = json.dumps(json_setting, sort_keys=True, ensure_ascii=False, indent=4)
    t = text.encode("utf-8")

    with open("setting.json", "wb") as fh:
        fh.write(t)

# JSON読み出し
def loadSetting(section):
    '''
    設定ファイル(setting.json)から読み取って、内容を返す。
    
    Parameters
    ----------
    section : str
        何のセクションを読み取るか？
        全天球イラストJPEGメタデータ埋め込み : 'convert_jpg_eqrect'

    Returns
    -------
    setting : dict
        設定情報。
        キーや内容はセクションによって異なります。
    '''
    with open('setting.json','r',encoding='utf-8') as f:
        setting = json.loads(f.read())

    # print(type(setting))

    return setting[section]

# 処理実行
def btn_execute_action(event):
    print("***** 全天球イラストJPEGメタデータ埋め込み処理開始 *****")
    # GUIインプット情報から数値変換
    FullPanoWidthPixels = int(txtVal_FullPanoWidthPixels.get())
    FullPanoHeightPixels = int(txtVal_FullPanoHeightPixels.get())
    CroppedAreaImageWidthPixels = int(txtVal_CroppedAreaImageWidthPixels.get())
    CroppedAreaImageHeightPixels = int(txtVal_CroppedAreaImageHeightPixels.get())
    CroppedAreaLeftPixels = int(txtVal_CroppedAreaLeftPixels.get())
    CroppedAreaTopPixels = int(txtVal_CroppedAreaTopPixels.get())
    jpgfilename = txtVal_filename.get()
    print("JPEG Image Filename = {}".format(jpgfilename))
    print("FullPanoPixels[W, H]         = [{}, {}]".format(FullPanoWidthPixels, FullPanoHeightPixels))
    print("CroppedAreaImagePixels[W, H] = [{}, {}]".format(CroppedAreaImageWidthPixels, CroppedAreaImageHeightPixels))
    print("CroppedAreaPixels[Left, Top] = [{}, {}]".format(CroppedAreaLeftPixels, CroppedAreaTopPixels))

    # Inputファイル名に「Equirectangular XMP」を付加して保存ファイル名とする
    out_jpgfilename = re.sub(r'\.(jpg|JPG)$', r'(Equirectangular XMP).\1', jpgfilename)

    # セグメント全走査完了(ループ脱出)フラグ
    flg = True
    # XMP埋め込み完了フラグ
    xXMP_W = False

    # 埋め込むxmpデータ
    xmp_b  = b'\xff\xe1\x04\x6e'   # APP1マーカー(1134byts + 2byte(マーカー分))
    xmp_b += b'\x68\x74\x74\x70\x3a\x2f\x2f\x6e\x73\x2e\x61\x64\x6f\x62\x65\x2e\x63\x6f\x6d\x2f\x78\x61\x70\x2f\x31\x2e\x30\x2f\x00\x3c\x3f\x78\x70\x61\x63\x6b\x65\x74\x20\x62\x65\x67\x69\x6e\x3d\x22\xef\xbb\xbf\x22\x20\x69\x64\x3d\x22\x57\x35\x4d'
    xmp_b += b'\x30\x4d\x70\x43\x65\x68\x69\x48\x7a\x72\x65\x53\x7a\x4e\x54\x63\x7a\x6b\x63\x39\x64\x22\x3f\x3e\x0a\x3c\x78\x3a\x78\x6d\x70\x6d\x65\x74\x61\x20\x78\x6d\x6c\x6e\x73\x3a\x78\x3d\x22\x61\x64\x6f\x62\x65\x3a\x6e\x73\x3a\x6d\x65\x74\x61'
    xmp_b += b'\x2f\x22\x20\x78\x6d\x70\x74\x6b\x3d\x22\x6d\x61\x6e\x61\x35\x34\x34\x20\x45\x71\x75\x69\x72\x65\x63\x74\x61\x6e\x67\x75\x6c\x61\x72\x20\x49\x6c\x6c\x75\x73\x74\x72\x61\x74\x69\x6f\x6e\x20\x56\x65\x72\x31\x2e\x31\x30\x22\x3e\x0a\x20'
    xmp_b += b'\x20\x3c\x72\x64\x66\x3a\x52\x44\x46\x20\x78\x6d\x6c\x6e\x73\x3a\x72\x64\x66\x3d\x22\x68\x74\x74\x70\x3a\x2f\x2f\x77\x77\x77\x2e\x77\x33\x2e\x6f\x72\x67\x2f\x31\x39\x39\x39\x2f\x30\x32\x2f\x32\x32\x2d\x72\x64\x66\x2d\x73\x79\x6e\x74'
    xmp_b += b'\x61\x78\x2d\x6e\x73\x23\x22\x3e\x0a\x20\x20\x20\x20\x3c\x72\x64\x66\x3a\x44\x65\x73\x63\x72\x69\x70\x74\x69\x6f\x6e\x20\x72\x64\x66\x3a\x61\x62\x6f\x75\x74\x3d\x22\x22\x20\x78\x6d\x6c\x6e\x73\x3a\x47\x50\x61\x6e\x6f\x3d\x22\x68\x74'
    xmp_b += b'\x74\x70\x3a\x2f\x2f\x6e\x73\x2e\x67\x6f\x6f\x67\x6c\x65\x2e\x63\x6f\x6d\x2f\x70\x68\x6f\x74\x6f\x73\x2f\x31\x2e\x30\x2f\x70\x61\x6e\x6f\x72\x61\x6d\x61\x2f\x22\x3e\x0a\x20\x20\x20\x20\x20\x20\x3c\x47\x50\x61\x6e\x6f\x3a\x50\x72\x6f'
    xmp_b += b'\x6a\x65\x63\x74\x69\x6f\x6e\x54\x79\x70\x65\x3e\x65\x71\x75\x69\x72\x65\x63\x74\x61\x6e\x67\x75\x6c\x61\x72\x3c\x2f\x47\x50\x61\x6e\x6f\x3a\x50\x72\x6f\x6a\x65\x63\x74\x69\x6f\x6e\x54\x79\x70\x65\x3e\x0a\x20\x20\x20\x20\x20\x20\x3c'
    xmp_b += b'\x47\x50\x61\x6e\x6f\x3a\x55\x73\x65\x50\x61\x6e\x6f\x72\x61\x6d\x61\x56\x69\x65\x77\x65\x72\x3e\x54\x72\x75\x65\x3c\x2f\x47\x50\x61\x6e\x6f\x3a\x55\x73\x65\x50\x61\x6e\x6f\x72\x61\x6d\x61\x56\x69\x65\x77\x65\x72\x3e\x0a'
    xmp_b +=  '      <GPano:CroppedAreaImageWidthPixels>{}</GPano:CroppedAreaImageWidthPixels>\n'.format(CroppedAreaImageWidthPixels).encode(encoding='utf-8')
    xmp_b +=  '      <GPano:CroppedAreaImageHeightPixels>{}</GPano:CroppedAreaImageHeightPixels>\n'.format(CroppedAreaImageHeightPixels).encode(encoding='utf-8')
    xmp_b +=  '      <GPano:FullPanoWidthPixels>{}</GPano:FullPanoWidthPixels>\n'.format(FullPanoWidthPixels).encode(encoding='utf-8')
    xmp_b +=  '      <GPano:FullPanoHeightPixels>{}</GPano:FullPanoHeightPixels>\n'.format(FullPanoHeightPixels).encode(encoding='utf-8')
    xmp_b +=  '      <GPano:CroppedAreaLeftPixels>{}</GPano:CroppedAreaLeftPixels>\n'.format(CroppedAreaLeftPixels).encode(encoding='utf-8')
    xmp_b +=  '      <GPano:CroppedAreaTopPixels>{}</GPano:CroppedAreaTopPixels>\n'.format(CroppedAreaTopPixels).encode(encoding='utf-8')
    xmp_b += b'\x20\x20\x20\x20\x20\x20\x3c\x47\x50\x61\x6e\x6f\x3a\x50\x6f\x73\x65\x50\x69\x74\x63\x68\x44\x65\x67\x72\x65\x65\x73\x3e\x30\x3c\x2f\x47\x50\x61\x6e\x6f\x3a\x50\x6f\x73\x65\x50\x69\x74\x63\x68\x44\x65\x67\x72\x65\x65\x73\x3e\x0a\x20\x20\x20\x20'
    xmp_b += b'\x20\x20\x3c\x47\x50\x61\x6e\x6f\x3a\x50\x6f\x73\x65\x52\x6f\x6c\x6c\x44\x65\x67\x72\x65\x65\x73\x3e\x30\x3c\x2f\x47\x50\x61\x6e\x6f\x3a\x50\x6f\x73\x65\x52\x6f\x6c\x6c\x44\x65\x67\x72\x65\x65\x73\x3e\x0a\x20\x20\x20\x20\x3c\x2f\x72\x64\x66\x3a'
    xmp_b += b'\x44\x65\x73\x63\x72\x69\x70\x74\x69\x6f\x6e\x3e\x0a\x20\x20\x3c\x2f\x72\x64\x66\x3a\x52\x44\x46\x3e\x0a\x3c\x2f\x78\x3a\x78\x6d\x70\x6d\x65\x74\x61\x3e\x0a\x3c\x3f\x78\x70\x61\x63\x6b\x65\x74\x20\x65\x6e\x64\x3d\x22\x72\x22\x3f\x3e\x0a'

    xmp_length = 1136-len(xmp_b)
    if xmp_length >= 0:
        print('APP1(Photosphere XMP) {}byte padding.'.format(xmp_length))
        for _ in range(xmp_length):
            xmp_b += b'\x20'
    else:
        print('確保しているバイトを越える設定値です。')
        return

    # ファイル読み込み開始
    with open(jpgfilename, mode='rb') as f:
        # 書き込みファイルのオープン
        with open(out_jpgfilename, mode='wb') as wf:
        
            while flg:
                # 2バイト取り出し
                a = struct.unpack('BB', f.read(2))

                # マーカーの発見($FF01～$FFFE)
                if (a[0]==255) and (a[1]>=1) and (a[1]<=254):
                    print('Marker: %s %s' % (format(a[0],'x'),format(a[1],'x')))
                    
                    # APP1マーカー($FFE1)
                    if (a[1]==225):
                        # 次の2バイトを読み込む:バイナリ
                        b = f.read(2)
                        # 2バイトバイナリをビッグエンディアンで解釈して数値変換(このマーカーの長さ)
                        lb = struct.unpack('>H', b)

                        buf = f.read(6)
                        # 次の6バイトが「Exif識別マーカー」だったら書き写す
                        if buf == b'\x45\x78\x69\x66\x00\x00':
                            print('APP1(Exif)マーカー(%dbyte)なので、書き写します'%(lb[0],))
                            # マーカー書き込み
                            for d in a:
                                wf.write(d.to_bytes(1, byteorder=sys.byteorder))
                            # 次の2バイト書き込み
                            wf.write(b)
                            # 次の6バイト書き込み
                            wf.write(buf)
                            # 残りのセグメントの長さだけ読み込む: バイナリ
                            buf = f.read(lb[0]-2-6)
                            # 残りのセグメント書き込み
                            wf.write(buf)

                            # もし、XMPデータの追記がまだだったらXMPデータを追記する
                            if not xXMP_W:
                                print('全天球情報(APP1 Photo Sphere XMP)を埋め込みます')
                                wf.write(xmp_b)
                                xXMP_W = True
                        # Exif以外のAPP1マーカーの場合
                        else:
                            print('APP1マーカー(%dbyte)ですがExifではないので、このセグメントはすっとばします'%(lb[0],))
                            # このセグメントはすっとばす
                            f.seek(lb[0]-2-6,1)
                        
                    # SOIマーカー($FFD8)
                    elif a[1]==216:
                        # そのまま書き写して次の2バイトへ
                        for d in a:
                            wf.write(d.to_bytes(1, byteorder=sys.byteorder))
                    # SOSマーカー($FFDA)
                    elif a[1]==218:
                        print('SOSマーカーなので、ここより後ろを全コピーします')
                        # そこより後ろをすべて書き写して、ループ抜けておしまい
                        buf = f.read()
                        # マーカー書き込み
                        for d in a:
                            wf.write(d.to_bytes(1, byteorder=sys.byteorder))
                        # 内容書き込み
                        wf.write(buf)
                        # ループ脱出
                        flg = False

                    # その他のマーカー
                    else:
                        # 次の2バイトを読み込む:バイナリ
                        b = f.read(2)
                        # 2バイトバイナリをビッグエンディアンで解釈して数値変換(このマーカーの長さ)
                        lb = struct.unpack('>H', b)
                        # セグメントの長さだけ読み込む: バイナリ
                        buf = f.read(lb[0]-2)
                        # マーカー書き込み
                        for d in a:
                            wf.write(d.to_bytes(1, byteorder=sys.byteorder))
                        # 次の2バイト書き込み
                        wf.write(b)
                        # セグメントの内容書き込み
                        wf.write(buf)

                        # もしAPP0マーカー($FFE0)で、まだxmpデータ書き出ししてなかったら、
                        # XMPデータを追記する
                        if (a[1]==224) and (not xXMP_W):
                            print('全天球情報(APP1 Photo Sphere XMP)を埋め込みます')
                            wf.write(xmp_b)
                            xXMP_W = True

    print('Output File: %s' % (out_jpgfilename, ))
    messagebox.showinfo('埋め込み完了','JPEGファイルに全天球情報を埋め込みました。\n出力ファイル名は{}です。'.format(out_jpgfilename))


def window_close_action():
    root.destroy()
    print('ウインドウ閉じる')


if __name__ == '__main__':
    # メインウインドウ生成
    root = tkinter.Tk()
    root.title(u"全天球イラストJPEGメタデータ埋め込み")
    root.resizable(False,False)     #ウィンドウサイズ変更の禁止　(x,y)・・・False：禁止　True：許可
    frm = ttk.Frame(root)
    frm.grid(column=0, row=0, sticky=tkinter.N+tkinter.S+tkinter.E+tkinter.W)

    # 初期設定値をsetting.jsonから読み込む
    setting = loadSetting('convert_jpg_eqrect')

    # ★★★★★★★★★★★★★★★
    # ★ スタティックテキスト ★
    # ★★★★★★★★★★★★★★★
    txt_title = ttk.Label(frm, text=u'全天球イラストJPEGメタデータ埋め込み', justify='left', padding='2')

    txtVal_filename = tkinter.StringVar()
    txtVal_filename.set(setting['txtVal_filename'])
    txt_filename = ttk.Label(frm, justify='left', textvariable=txtVal_filename, padding='2', width=30)
    txt_FullPanoWidthPixels = ttk.Label(frm, text=u'FullPanoWidthPixels', justify='left', padding='2')
    txt_FullPanoHeightPixels = ttk.Label(frm, text=u'FullPanoHeightPixels', justify='left', padding='2')
    txt_CroppedAreaImageWidthPixels = ttk.Label(frm, text=u'CroppedAreaImageWidthPixels', justify='left', padding='2')
    txt_CroppedAreaImageHeightPixels = ttk.Label(frm, text=u'CroppedAreaImageHeightPixels', justify='left', padding='2')
    txt_CroppedAreaLeftPixels = ttk.Label(frm, text=u'CroppedAreaLeftPixels', justify='left', padding='2')
    txt_CroppedAreaTopPixels = ttk.Label(frm, text=u'CroppedAreaTopPixels', justify='left', padding='2')

    # ★★★★★★★★★★★★★★
    # ★ インプットテキスト ★
    # ★★★★★★★★★★★★★★
    txtVal_FullPanoWidthPixels = tkinter.StringVar()
    txtVal_FullPanoWidthPixels.set(setting['txtVal_FullPanoWidthPixels'])
    input_FullPanoWidthPixels = ttk.Entry(frm, width=6, justify='left', textvariable=txtVal_FullPanoWidthPixels)

    txtVal_FullPanoHeightPixels = tkinter.StringVar()
    txtVal_FullPanoHeightPixels.set(setting['txtVal_FullPanoHeightPixels'])
    input_FullPanoHeightPixels = ttk.Entry(frm, width=6, justify='left', textvariable=txtVal_FullPanoHeightPixels)

    txtVal_CroppedAreaImageWidthPixels = tkinter.StringVar()
    txtVal_CroppedAreaImageWidthPixels.set(setting['txtVal_CroppedAreaImageWidthPixels'])
    input_CroppedAreaImageWidthPixels = ttk.Entry(frm, width=6, justify='left', textvariable=txtVal_CroppedAreaImageWidthPixels)

    txtVal_CroppedAreaImageHeightPixels = tkinter.StringVar()
    txtVal_CroppedAreaImageHeightPixels.set(setting['txtVal_CroppedAreaImageHeightPixels'])
    input_CroppedAreaImageHeightPixels = ttk.Entry(frm, width=6, justify='left', textvariable=txtVal_CroppedAreaImageHeightPixels)

    txtVal_CroppedAreaLeftPixels = tkinter.StringVar()
    txtVal_CroppedAreaLeftPixels.set(setting['txtVal_CroppedAreaLeftPixels'])
    input_CroppedAreaLeftPixels = ttk.Entry(frm, width=6, justify='left', textvariable=txtVal_CroppedAreaLeftPixels)

    txtVal_CroppedAreaTopPixels = tkinter.StringVar()
    txtVal_CroppedAreaTopPixels.set(setting['txtVal_CroppedAreaTopPixels'])
    input_CroppedAreaTopPixels = ttk.Entry(frm, width=6, justify='left', textvariable=txtVal_CroppedAreaTopPixels)

    # ★★★★★★★
    # ★ ボタン ★
    # ★★★★★★★
    btn_fileopen = ttk.Button(frm, text=u'全天球イラスト選択...', command=btn_fileopen_callback)
    btn_execute = ttk.Button(frm, text=u'メタデータ埋め込み')
    btn_savesetting = ttk.Button(frm, text=u'設定保存', command=btn_saveSetting_action)
    
    # ★★★★★★★★
    # ★ イベント ★
    # ★★★★★★★★
    btn_execute.bind("<ButtonRelease-1>", btn_execute_action) 

    # ★★★★★★★★★
    # ★ レイアウト ★
    # ★★★★★★★★★
    txt_title.grid(row=0, column=0, columnspan=2, sticky='W')
    btn_fileopen.grid(row=1, column=0, sticky='E')
    txt_filename.grid(row=1, column=1, sticky='W')
    txt_FullPanoWidthPixels.grid(row=2, column=0, sticky='E')
    input_FullPanoWidthPixels.grid(row=2, column=1, sticky='W')
    txt_FullPanoHeightPixels.grid(row=3, column=0, sticky='E')
    input_FullPanoHeightPixels.grid(row=3, column=1, sticky='W')
    txt_CroppedAreaImageWidthPixels.grid(row=4, column=0, sticky='E')
    input_CroppedAreaImageWidthPixels.grid(row=4, column=1, sticky='W')
    txt_CroppedAreaImageHeightPixels.grid(row=5, column=0, sticky='E')
    input_CroppedAreaImageHeightPixels.grid(row=5, column=1, sticky='W')
    txt_CroppedAreaLeftPixels.grid(row=6, column=0, sticky='E')
    input_CroppedAreaLeftPixels.grid(row=6, column=1, sticky='W')
    txt_CroppedAreaTopPixels.grid(row=7, column=0, sticky='E')
    input_CroppedAreaTopPixels.grid(row=7, column=1, sticky='W')
    btn_savesetting.grid(row=8, column=0, sticky='W')
    btn_execute.grid(row=8, column=1, sticky='E')

    root.protocol("WM_DELETE_WINDOW", window_close_action)
    root.mainloop()
