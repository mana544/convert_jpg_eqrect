# -*- coding: utf-8 -*-
import struct
import sys
import os, tkinter, tkinter.filedialog, tkinter.messagebox
import re

'''
JPEGファイル内に全天球情報(APP1 Photo Sphere XMP)を埋め込む。
APP0(JFIF)もしくはAPP1(Exif)の直後に埋め込みます。
Exif以外のAPP1(xmp)セグメントが元々埋め込まれている場合は、
その情報は破棄します。

【動作環境(使用モジュール)】
Python(Anaconda) 3.6.4(5.1.0)
tkinter 8.6
'''
# ▼▼▼ 設定値ココカラ ▼▼▼
# jpgfilename = "正距円筒図グリッド.jpg"
# out_jpgfilename = "正距円筒図グリッド_out.jpg"
# ▲▲▲ 設定値ココマデ ▲▲▲

# ファイル選択ダイアログの表示
root = tkinter.Tk()
root.withdraw()
fTyp = [("JPEG File","*.jpg")]
iDir = os.path.abspath(os.path.dirname(__file__))
# tkinter.messagebox.showinfo('○×プログラム','処理ファイルを選択してください！')
jpgfilename = tkinter.filedialog.askopenfilename(filetypes = fTyp,initialdir = iDir)
# Inputファイル名に「Equirectangular XMP」を付加して保存ファイル名とする
out_jpgfilename = re.sub(r'\.(jpg|JPG)$', r'(Equirectangular XMP).\1', jpgfilename)

# セグメント全走査完了(ループ脱出)フラグ
flg = True
# XMP埋め込み完了フラグ
xXMP_W = False

# 埋め込むxmpデータ読み込み
with open("xmp_raw", mode='rb') as xf:
    xmp_b = xf.read()


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



