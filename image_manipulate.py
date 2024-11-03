import json
import os
import customtkinter as ctk
from tkinter import Canvas, messagebox
from PIL import Image, ImageDraw, ImageFont, ImageTk
from setting import *


class JsonEkle: #Json İçindeki Verilere Ulaşıp Kontrol Eder.

    def update_json_file(key, value):
        file_path = DosyaKonumu().dosya_konumunu_al("data_json")
        # Eğer dosya varsa içeriği oku, yoksa boş bir dictionary oluştur
        if os.path.exists(file_path):
            with open(file_path, "r") as json_file:
                try:
                    data = json.load(json_file)
                except json.JSONDecodeError:
                    data = {}
        else:
            data = {}

        # Anahtarı güncelle veya ekle
        data[key] = value

        # Dosyayı güncelle
        with open(file_path, "w") as json_file:
            json.dump(data, json_file, indent=4)

    def loads_ekle(loads):
        
        with open(DosyaKonumu().dosya_konumunu_al("data_json"), "r", encoding="utf-8") as dosya:
            veri = json.load(dosya)

            if loads in veri["Loads"]:
                pass
            else:
                veri["Loads"].append(loads)

        with open (DosyaKonumu().dosya_konumunu_al("data_json"), "w", encoding="utf-8") as dosya:
            json.dump(veri,dosya,ensure_ascii=False,indent=4)

    def Supports_ekle(self,supporttype,supportside,lenght):

        self.supporttype = supporttype
        self.supportside= supportside
        self.lenght = lenght

        for supportlar in JsonEkle.bilgi_oku("Supports"):# self.lenght konumunda başka bir support var ise öncekini siler 
            if float(supportlar[2])== float(self.lenght):
                JsonEkle.bilgi_sil("Supports",supportlar)       
        
        support_anlık = []
        support_anlık.append(self.supporttype)
        support_anlık.append(self.supportside)
        support_anlık.append(self.lenght)        
        
        
        with open(DosyaKonumu().dosya_konumunu_al("data_json"),"r") as dosya:
            veri = json.load(dosya)
            veri["Supports"].append(support_anlık)

        with open(DosyaKonumu().dosya_konumunu_al("data_json"), "w", encoding="utf-8") as dosya:
            json.dump(veri, dosya, ensure_ascii=False, indent=4)

    def veri_ekle(self,eklenilecek_yer, eklenilecek):

        with open(DosyaKonumu().dosya_konumunu_al("data_json"), "r", encoding="utf-8") as dosya:
            veri = json.load(dosya)

            veri[eklenilecek_yer].append(eklenilecek)
        with open(DosyaKonumu().dosya_konumunu_al("data_json"), "w", encoding="utf-8") as dosya:
            json.dump(veri, dosya, ensure_ascii=False, indent=4)

    def bilgi_oku(aranan):
        
        file_path = DosyaKonumu().dosya_konumunu_al("data_json")
        with open(file_path, "r") as json_file:
            data = json.load(json_file)
        aranan_value = data.get(aranan)

        return aranan_value

    def bilgi_sil(ana_veri,silinecek_veri):

        file_path = DosyaKonumu().dosya_konumunu_al("data_json")
        with open(file_path, 'r') as file:
            data = json.load(file)

        data[ana_veri] = [load for load in data[ana_veri] if silinecek_veri != load]

        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)

class ResmiGuncelle: #Ekrana Resmi Yazdırır ardından (Yazı,Supports,Loads) varsa ekler.
    def __init__(self,parent):
        self.parent = parent    
        self.parent.original = Image.open(self.parent.ilk_resim_olustur())
        self.parent.image = self.parent.original #resimi çekiyor

        YaziEkle(self.parent)#Yazıları Ekler
        SupportsResimEkle(self.parent)#Supportsları Ekler
        LoadsResimEkle(self.parent)#Loadsları Ekler
        

class YaziEkle: #Resimdeki Kiriş Uzunluğu Bilgisini Ekranda Gösterir.
    def __init__(self, parent):
        self.parent = parent

        text1= str(JsonEkle.bilgi_oku("Beam Lenght"))
        text2 = BirimiDegistir(JsonEkle.bilgi_oku("Length Unit"),"1").degistir()
        self.text = text1 + " " + text2 

        self.add_text_to_image()

    def add_text_to_image(self):
        # Önceki metni ve çizimleri temizle
        self.parent.image_output.delete("text")
        # Resmin boyutlarını al
        width, height = self.parent.image.size
        # Çizim nesnesini oluştur
        draw = ImageDraw.Draw(self.parent.image)
        # Yazı tipi ve boyutunu ayarla
        font = ImageFont.truetype("arial", 35)
        text_color = (255, 255, 255)  # Beyaz renk (RGB)

        # Metnin yazılacağı konumu hesapla (ortada)
        text_bbox = draw.textbbox((0, 0), self.text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
               
        x = 950- text_width/2     # ekranda gözüken kiriş uzunluğunun ekranda konumlandırılması
        y= 800 -text_height/2
        
        # Metni resmin üzerine yaz
        draw.text((x,y), self.text, fill=text_color, font=font)
        # Resmi güncelle
        
        self.parent.image_tk = ImageTk.PhotoImage(self.parent.image)
        self.parent.place_image()
        
class LoadsResimEkle: #Resimdeki Loads'ları Ekranda Gösterir.

    def __init__(self,parent):
        self.parent = parent
        self.kiris_uzunluk =float(JsonEkle.bilgi_oku("Beam Lenght"))

        for loadslar in JsonEkle.bilgi_oku("Loads"):

            self.loadtype= loadslar[0]

            if self.loadtype == "Point Load":
                self.lenght_point_load = loadslar[1]
                self.force_point_load = loadslar[2]
                self.angle_point_load = loadslar[3]
                self.add_PointImage_to_Image()

            if self.loadtype == "Bending Moment":
                self.lenght_bending_load = loadslar[1]
                self.force_bending_load = loadslar[2]
                self.add_BendingMomentImage_to_Image()
            
            if self.loadtype == "Distributed Load":
                self.lenght_distr_load1 = loadslar[1]
                self.lenght_distr_load2 = loadslar[2]
                self.force_distr_load = loadslar[3]
                self.add_DistributedLoadImage_to_Image()

    def add_PointImage_to_Image(self):

        x_position= int(185+ 1250*(float(self.lenght_point_load)/self.kiris_uzunluk))

        if int(self.force_point_load)>=0:
            overlay_position =(x_position,415)
            overlay_image_path = DosyaKonumu().dosya_konumunu_al("point_load")

        if int(self.force_point_load)<0:
            overlay_position =(x_position,436)
            overlay_image_path = DosyaKonumu().dosya_konumunu_al("point_load_negative")

        if int(self.angle_point_load)<=180:
            overlay_image = Image.open(overlay_image_path)
            overlay_image = overlay_image.rotate(-90+(int(self.angle_point_load)))
            mask = overlay_image.split()[3]
            self.parent.image.paste(overlay_image,overlay_position,mask)

            self.parent.place_image()

    def add_BendingMomentImage_to_Image(self):

        x_position= int(248+ 1253*(float(self.lenght_bending_load)/self.kiris_uzunluk))
        overlay_position =(x_position,510)
        if int(self.force_bending_load)>=0: 
            overlay_image_path = DosyaKonumu().dosya_konumunu_al("moment_load") 
        if int(self.force_bending_load)<0:
            overlay_image_path = DosyaKonumu().dosya_konumunu_al("moment_load_negative") 

        overlay_image = Image.open(overlay_image_path)

        mask = overlay_image.split()[3]
        self.parent.image.paste(overlay_image,overlay_position,mask)

        self.parent.place_image()

    def add_DistributedLoadImage_to_Image(self):

            listee = []
            listee.append(self.lenght_distr_load1)
            listee.append(self.lenght_distr_load2)

            line_liste=[]
            
            for x in listee:
                x_position= int(223+ 1250*(float(x)/self.kiris_uzunluk))
                line_liste.append((x_position))

                if int(self.force_distr_load)>=0:
                    overlay_position =(x_position,413)
                    overlay_image_path = DosyaKonumu().dosya_konumunu_al("distr_load") 

                if int(self.force_distr_load)<0:
                    overlay_position =(x_position,569)
                    overlay_image_path = DosyaKonumu().dosya_konumunu_al("distr_load_negative") 
            
                overlay_image = Image.open(overlay_image_path)

                mask = overlay_image.split()[3]
                self.parent.image.paste(overlay_image,overlay_position,mask)

                self.parent.place_image()
 

            if float(self.force_distr_load)<0:
                y_position = 723
            else:
                y_position = 425
            # Start and End positions for the line
            start_position = ((int(line_liste[0])+108), y_position)
            end_position = ((int(line_liste[1])+116), y_position)

            # Resim üzerine çizim yapmak için ImageDraw kullan
            draw = ImageDraw.Draw(self.parent.image)

            # Çizgi rengi ve kalınlığı
            line_color = (237,28,36)  # Yeşil renk
            line_width = 10 # Kalınlık

            # İki nokta arasında çizgi çiz
            draw.line([start_position, end_position], fill=line_color, width=line_width)

        # Yeni resmi yerleştir
            self.parent.place_image()

class SupportsResimEkle: #Resimdeki Supports'ları Ekranda Gösterir.

    def __init__(self,parent):
        self.parent = parent

        for supportlar in JsonEkle.bilgi_oku("Supports"):
            if (float(supportlar[-1])<=float(JsonEkle.bilgi_oku("Beam Lenght")) and float(supportlar[-1])<=float(JsonEkle.bilgi_oku("Beam Lenght"))) or supportlar[1]=="On The Right": # girilen mesafe eğer kiriş dışında ise ekrana yazdırmayacak
                
                self.supporttype = supportlar[0]
                self.type = supportlar[1]
                self.length = supportlar[-1]
                self.add_supports_to_image()

    def add_supports_to_image(self):

        kiris_uzunluk =float(JsonEkle.bilgi_oku("Beam Lenght"))  

        if self.type=="On The Right":

            x_position = 1440
        else:
            x_position= int(190+ 1250*(float(self.length)/kiris_uzunluk))

        overlay_position =(x_position,530)

        if self.supporttype == "fixed" and self.type =="On The Left":
            overlay_position = (190,470)

        if self.supporttype == "fixed" and self.type =="On The Right":
            overlay_position = (1435,470)
            self.supporttype = "fixed_aynalanmıs"

        overlay_image_path = DosyaKonumu().dosya_konumunu_al(self.supporttype)
        
        overlay_image = Image.open(overlay_image_path)

        mask = overlay_image.split()[3]
        self.parent.image.paste(overlay_image,overlay_position,mask)

        self.parent.place_image()

class AnaliziBaslatButon(ctk.CTkFrame): #Program İlk Çalıştığında "Analize Başla" Butonu

    def __init__(self,parent, import_func):
        super().__init__(master = parent)
        self.grid(column=0, columnspan = 2, row=0, sticky='nswe')

        self.import_func = import_func
           
        #Analize Başla butonu
        ctk.CTkButton(self, 
                      text=TEXT_01,
                      command=self.open_dialog, 
                      width=250, 
                      height=75, 
                      font=('Arial', 20)).pack(expand=True) 




        #resim linkini alıyor
    def open_dialog(self):
        self.import_func()

class ImageOutput(Canvas): #Resmi Ekranda Gösteriyor   
    def __init__(self,parent, resize_image):
         
        super().__init__(master= parent, background= BACKGROUND_COLOR, bd=0, highlightthickness =0, relief ='ridge')
        self.grid(row=0, column=1, sticky='nsew',padx=10,pady =10)
        self.bind('<Configure>', resize_image)
        
class AnaliziBitirmeButonu(ctk.CTkButton): #Kapatma Butonu
    def __init__(self,parent, close_func):
        super().__init__(master=parent,
        text='x',
        command=close_func,
        text_color= WHITE, 
        fg_color= 'transparent', 
        width=40, 
        height=40
        ,corner_radius=0,
        hover_color=DARK_GREY)
        self.place(relx=0.99, rely=0.05, anchor= 'ne')

class Uyari: #Uyarıları Ekranda Gösteriyor
    def __init__(self,UyariMesaji,baslik):
        messagebox.showinfo(baslik, UyariMesaji)

class BirimiDegistir: #Birim Değişimleri Yapıyor.
    def __init__(self,value,info):
        self.value = value
        self.info = info

        self.birimler = [["Milimeter (mm)","(mm)","mm",1],
                    ['Centimeter (cm)',"(cm)","cm",10],
                    ['Decimeter (dm)',"(dm)","dm",100],
                    ['Meter (m)',"(m)","m",1000],
                    ['Inch (in)',"(in)","in",25.4],
                    ['Yard (yd)',"(yd)","yd",914.4],
                    ['Foot (ft)',"(ft)","ft",304.8],
                    ['Newton (N)',"(N)","N",1],
                    ['Kilonewton (kN)',"(kN)","kN",1000],
                    ['Meganewton (MN)',"(MN)","MN",1000000],
                    ['Gram-force (gf)',"(gf)","gf",0.00980665],
                    ['Kilogram-force (kgF)',"(kgF)","kgF",9.80665],
                    ['Ton-force (tf)',"(tf)","tf",9806.65],
                    ['Poundal (pdl)',"(pdl)","N",1],
                    ['Pound-force (lbf)',"(lbf)","lbf",4.4482216],
                    ['Kip-force (kipf)',"(kipf)","kipf",4448.2216153]]
        
    def degistir(self):
        for liste in self.birimler:
            if self.value== liste[0]:
                if self.info=="0":
                    return liste[1]
                if self.info=="1":
                    return liste[2]
                if self.info=="2":
                    return liste[3]

class DataReset: #Verileri Başlangıçtaki Konumuna Getiriyor.
    def __init__(self):
        JsonEkle.update_json_file("Beam Lenght","10")
        JsonEkle.update_json_file("Moment Of Inertia",10000000)
        JsonEkle.update_json_file("Young's Module",200000)
        JsonEkle.update_json_file("Length Unit", "Meter (m)")
        JsonEkle.update_json_file("Force Unit", "Newton (N)")
        JsonEkle.update_json_file("Moment Unit", "(Nm)")
        JsonEkle.update_json_file("Load Magnitude Unit", "(N/m)")
        JsonEkle.update_json_file("Supports", [])
        JsonEkle.update_json_file("Loads", [])
        JsonEkle.update_json_file("Hesaplanmasi istenenler", ["Bending Moment Diagram (BMD)","Shear Force Diagram (SFD)"])

class DosyaKonumu: #Dosya Konumlarını Veriyor.
    def __init__(self):

        self.dosya_yolu = os.path.abspath(__file__)
        self.dizin_yolu = os.path.dirname(self.dosya_yolu)

        self.data_json = f"{self.dizin_yolu}/data.json"


        self.support_pin_showing_location = f"{self.dizin_yolu}/img/supports/0.png"
        self.support_roller_showing_location = f"{self.dizin_yolu}/img/supports/1.png"
        self.support_fix_showing_location = f"{self.dizin_yolu}/img/supports/2.png"

        self.load_point_showing_location = f"{self.dizin_yolu}/img/Loads/0.png"
        self.load_moment_showing_location = f"{self.dizin_yolu}/img/Loads/1.png"
        self.load_distload_showing_location = f"{self.dizin_yolu}/img/Loads/2.png"

        self.on_button = f'{self.dizin_yolu}/img/other/on.png'
        self.off_button = f'{self.dizin_yolu}/img/other/off.png'

        self.add_image_load_point_positive = f'{self.dizin_yolu}/img/Loads/eklenecek resim/point_load.png'
        self.add_image_load_point_negative = f'{self.dizin_yolu}/img/Loads/eklenecek resim/point_load_negative.png'
        self.add_image_load_moment_positive = f'{self.dizin_yolu}/img/Loads/eklenecek resim/moment_load.png'
        self.add_image_load_moment_negative = f'{self.dizin_yolu}/img/Loads/eklenecek resim/moment_load_negative.png'
        self.add_image_load_distributed_positive = f'{self.dizin_yolu}/img/Loads/eklenecek resim/distr_load.png'
        self.add_image_load_distributed_negative = f'{self.dizin_yolu}/img/Loads/eklenecek resim/distr_load_negative.png'

        self.support_fixxed_adding_location = f'{self.dizin_yolu}/img/supports/eklenecek resim/fixed.png'
        self.support_fixxed_mirror_adding_location = f'{self.dizin_yolu}/img/supports/eklenecek resim/fixed_aynalanmıs.png'
        self.support_pin_adding_location = f'{self.dizin_yolu}/img/supports/eklenecek resim/pin.png'
        self.support_roller_adding_location = f'{self.dizin_yolu}/img/supports/eklenecek resim/roller.png'
        
    def dosya_konumunu_al(self, dosya):

        if dosya == "pin_showing":
            return self.support_pin_showing_location
        if dosya == "roller_showing":
            return self.support_roller_showing_location
        if dosya == "fix_showing":
            return self.support_fix_showing_location
        
        if dosya == "point_showing":
            return self.load_point_showing_location
        if dosya == "moment_showing":
            return self.load_moment_showing_location
        if dosya == "distload_showing":
            return self.load_distload_showing_location
        
        if dosya == "on_button":
            return self.on_button
        if dosya == "off_button":
            return self.off_button
        
        if dosya == "data_json":
            return self.data_json
        
        if dosya == "point_load":
            return self.add_image_load_point_positive
        if dosya == "point_load_negative":
            return self.add_image_load_point_negative
        if dosya == "moment_load":
            return self.add_image_load_moment_positive
        if dosya == "moment_load_negative":
            return self.add_image_load_moment_negative     
        if dosya == "distr_load":
            return self.add_image_load_distributed_positive
        if dosya == "distr_load_negative":
            return self.add_image_load_distributed_negative

        if dosya == "fixed":
            return self.support_fixxed_adding_location
        if dosya == "fixed_aynalanmıs":
            return self.support_fixxed_mirror_adding_location
        if dosya == "pin":
            return self.support_pin_adding_location 
        if dosya == "roller":
            return self.support_roller_adding_location


