import customtkinter as ctk
from menu import Menu #Custom Library
from PIL import Image, ImageTk, ImageDraw
from image_manipulate import * #Custom Library
import io


class App(ctk.CTk):

    def __init__(self):
        super().__init__()

        musa = "ENG"
        #tasarım
        ctk.set_appearance_mode('dark')
        self.geometry('1500x750')
        self.title(TEXT_00)
        self.minsize(1400,700)
        
        #layout
        self.rowconfigure(0,weight=1)
        self.columnconfigure(0,weight=2, uniform= 'a')
        self.columnconfigure(1,weight=6, uniform= 'a')

        self.shared_vars = ["","","","","","","","",""]
        
        # Değişken Verilerin Heryerde Kullanabilmesi için Database oluşturuldu.
        self.shared_var_lenght_unit = ctk.StringVar(value=BirimiDegistir(JsonEkle.bilgi_oku("Length Unit"),"0").degistir())
        self.shared_var_force_unit = ctk.StringVar(value=BirimiDegistir(JsonEkle.bilgi_oku("Force Unit"),"0").degistir())
        self.shared_var_moment_unit = ctk.StringVar(value=JsonEkle.bilgi_oku("Moment Unit"))
        self.shared_var_load_mangnitude_unit = ctk.StringVar(value=JsonEkle.bilgi_oku("Load Magnitude Unit"))
        self.shared_var_beam_lenght = ctk.StringVar(value=JsonEkle.bilgi_oku("Beam Lenght"))
        self.shared_var_moment_of_inertia_unit = ctk.StringVar(value=JsonEkle.bilgi_oku("Moment Of Inertia Unit"))
        self.shared_var_youngs_module_unit = ctk.StringVar(value=JsonEkle.bilgi_oku("Young's Module Unit"))
        self.shared_var_moment_of_inertia_lenght = ctk.StringVar(value=JsonEkle.bilgi_oku("Moment Of Inertia"))
        self.shared_var_youngs_module_lenght = ctk.StringVar(value=JsonEkle.bilgi_oku("Young's Module"))
        
        self.shared_vars[0] = self.shared_var_lenght_unit
        self.shared_vars[1] = self.shared_var_force_unit
        self.shared_vars[2] = self.shared_var_moment_unit
        self.shared_vars[3] = self.shared_var_load_mangnitude_unit
        self.shared_vars[4] = self.shared_var_beam_lenght
        self.shared_vars[5] = self.shared_var_moment_of_inertia_unit
        self.shared_vars[6] = self.shared_var_youngs_module_unit
        self.shared_vars[7] = self.shared_var_moment_of_inertia_lenght
        self.shared_vars[8] = self.shared_var_youngs_module_lenght

        #Widgets
        self.image_import = AnaliziBaslatButon(self, self.import_image) #Analizi Başlat Butonunu Ekranda Gösterir. Butona Basıldığında Devam Eder.

        #run
        self.mainloop()

    def ilk_resim_olustur(self): #En baştaki Resmi Oluşturur.

        # Resim boyutları
        width = 1920
        height = 1080

        background_color = (59,59,59) #Arka plan rengi 

        image = Image.new("RGB", (width, height), background_color)
        draw = ImageDraw.Draw(image)

        start_x = 334  #Soldan uzaklık
        start_y = 565  #Yukarıdan uzaklık
        line_length = 1254  #Çizgi uzunluğu
        line_thickness = 20  #Çizgi kalınlığı
        line_color = (0, 0, 0)  

        end_x = start_x + line_length

        draw.rectangle([start_x, start_y, end_x, start_y + line_thickness], fill=line_color)
        image_bytes = io.BytesIO()
        image.save(image_bytes, format='PNG')
        image_bytes.seek(0)  
        
        return image_bytes
        
    def import_image(self):

        self.original = Image.open(self.ilk_resim_olustur())


        self.image = self.original #resimi çekiyor
        self.image_ratio = self.image.size[0]/self.image.size[1]
        self.image_tk = ImageTk.PhotoImage(self.image) #resimi çekiyor

        self.image_import.grid_forget()         #buton kaldır  
        self.image_output = ImageOutput(self, self.resize_image)   #Resmi Ekranda Gösterir
        self.close_button = AnaliziBitirmeButonu(self, self.programı_kapat)  #kapatma butonu eklendi
        
        self.menu = Menu(self,self.shared_vars,self.resmi_guncelle,"0")  

        ResmiGuncelle(self) #Ekranda İlk kiriş uzunluğunu yazıyor (10 m) ve Eğer Json İçinde Veri Varsa Onlarıda Ekranda Gösteriyor.

    def resmi_guncelle(self,adress,tab):#Değişiklik Olduğunda Ekranı Ve Menuyü Günceller
            
        ResmiGuncelle(self) #Resimi Günceller

        if adress == "reset_menu":#Menüyü Günceller
            self.menu = Menu(self, self.shared_vars, self.resmi_guncelle, tab)
            
        self.close_button = AnaliziBitirmeButonu(self, self.programı_kapat)
       
    def programı_kapat(self): #Programı Kapatıp "Analizi Başlat" Ekranına Gönderir.
        self.image_output.grid_forget()
        self.image_output.place_forget()
        self.menu.grid_forget()
        self.image_import = AnaliziBaslatButon(self, self.import_image) #"Analizi Başlat" Ekranına Gönderir.
        DataReset() #kapatma butonuna basıldığında json verilerini default yapar

    def resize_image(self, event): #Ekran Boyutu Değiştirildiğinde Resim Boyutunu korur.

        # resim oranının bozulmaması için kodlar 58 ve 59. satırdada var.
        canvas_ratio = event.width/event.height
        #update canvas attributes
        self.canvas_width = event.width
        self.canvas_height = event.height
 
        if canvas_ratio > self.image_ratio:
            self.image_height = int(event.height())
            self.image_width = int(self.image_height*self.image_ratio)
        else:
            self.image_width = int(event.width)
            self.image_height = int(self.image_width/self.image_ratio)

        
        
        self.place_image()

    def place_image(self):

        self.image_output.delete("all")
        resized_image = self.image.resize((self.image_width,self.image_height))
        self.image_tk = ImageTk.PhotoImage(resized_image)
        self.image_output.create_image(self.canvas_width/2, self.canvas_height/2, image=self.image_tk)  #resmi yazdırıyor



App()
DataReset()