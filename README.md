# convert_jpg_eqrect
正距円筒図法(Equirectangular)で描いたイラスト(JPEG画像)にPhoto Sphere XMPメタデータを挿入します

---
## 概要
JPEGファイルのヘッダー内(APP1)に全天球情報(Photo Sphere XMP)を埋め込みます。これによって、正距円筒図法(Equirectangular)に則って描かれたイラストは、360°再生対応サービスでVRモード(全天球)再生するようになります。([参考記事](https://www.facebook.com/mana544/posts/1941667462592741))

埋め込む位置は、元から存在するAPP0(JFIF)もしくはAPP1(Exif)の直後に埋め込みます。Exif以外のAPP1(xmp)セグメントが元々埋め込まれている場合は、その情報は破棄します。

## 動作環境(使用モジュール)
* Python(Anaconda) 3.6.4(5.1.0)
* tkinter 8.6

## 今後やること
いろんな画像サイズ対応(今のところ5376 X 2688のみ対応です)

## 免責事項
このプログラムはそもそも展開用に書いたものではないので、ドキュメント等はありません(書く予定もありません)。従って、備忘録的に書いたソース内のコメントを頼りに、Pythonコードを解析できる人のみ利用してください。  
ライセンスはGPLに準拠します。利用の際は、作者は一切の責任(サポート等)を負わないものとします。  
もともと作者(わたなべ:mana544)が全天球イラスト制作用に個人的に描いた汎用性のないスクリプトなので、ソース(構造含む)が汚いのはご容赦を。合間見てちょぼちょぼ修正入れていきます。Fork大歓迎(誰か抽象化してクラスで書いてくれないかな…)

