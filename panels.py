import customtkinter as ctk
import tkinter as tk
from tkinter import PhotoImage
from setting import * #Custom Library
from image_manipulate import * #Custom Library
from PIL import Image, ImageTk
from customtkinter import CTkImage




class Panel(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(master=parent, fg_color= DARK_GREY)
        self.pack(fill = 'x', pady = 4, ipady=8)

class EntryPanel(ctk.CTkFrame):
        
    def __init__(self, parent, text, shared_vars,fonksiyon):
        super().__init__(parent)
        self.text = text
        self.shared_var_lenght_unit = shared_vars[0]
        self.shared_var_force_unit = shared_vars[1]
        self.shared_var_moment_unit = shared_vars[2]
        self.shared_var_loads_force_unit = shared_vars[3]
        self.shared_var_beam_lenght = shared_vars[4]
        self.shared_vars = shared_vars
        self.fonksiyon=fonksiyon

        # Bir frame içinde iki label hizalayacağız
        self.label_frame = ctk.CTkFrame(master=self, fg_color="transparent")
        self.label_frame.pack(fill='x', pady=4, padx=4)

        # İlk yazı label
        self.label = ctk.CTkLabel(master=self.label_frame, text=text, font=('Arial', 15))
        self.label.pack(side='left', anchor='w', padx=4, pady=4)

        # Meter değişen birim
        if self.text == TEXT_08 or self.text == TEXT_24 or self.text == TEXT_28 or self.text == TEXT_29:
            self.meter_label = ctk.CTkLabel(master=self.label_frame, textvariable=self.shared_var_lenght_unit, font=('Arial', 12))
            self.meter_label.pack(side='left', anchor='w', padx=0, pady=4)

        #Point Load değişen birimler
        elif self.text ==  TEXT_25:
            self.meter_label = ctk.CTkLabel(master=self.label_frame, textvariable=self.shared_var_force_unit, font=('Arial', 12))
            self.meter_label.pack(side='left', anchor='w', padx=0, pady=4)

        #distributed Load değişen birimler
        elif self.text ==  TEXT_30:
            self.meter_label = ctk.CTkLabel(master=self.label_frame, textvariable=self.shared_var_loads_force_unit, font=('Arial', 12))
            self.meter_label.pack(side='left', anchor='w', padx=0, pady=4)

        #Moment Load değişen birimler
        elif self.text == TEXT_27:
            
            self.meter_label = ctk.CTkLabel(master=self.label_frame, textvariable=self.shared_var_moment_unit, font=('Arial', 12))
            self.meter_label.pack(side='left', anchor='w', padx=0, pady=4)


        self.entry_EntryPanel = ctk.CTkEntry(self)
        self.entry_EntryPanel.pack(side='left', fill='x', expand=True, padx=4, pady=4)

        #Kiriş Uzunluğunu anlık olarak json dosyasına ve ekrana yazdırmak için fonksiyonu çalıştırır..
        if self.text == TEXT_08:
            self.entry_EntryPanel.insert(0, JsonEkle.bilgi_oku("Beam Lenght")) 
            #self.entry_EntryPanel.bind("<FocusOut>", self.on_focus_out)
            self.entry_EntryPanel.bind("<KeyRelease>", self.on_focus_out)

        #Açı stock değer olarak 90 derece ayarlandı.
        if self.text == TEXT_26:
            self.entry_EntryPanel.insert(0, "90")

        self.pack(fill='x', pady=4, padx=4)
        
    def on_focus_out(self, event):
        if self.text == TEXT_08:
            self.entry_degeri = (self.entry_EntryPanel.get())

            if "," in str(self.entry_degeri):
                self.entry_degeri = self.entry_degeri.replace(",", ".")

            self.shared_var_beam_lenght.set(self.entry_degeri)
            JsonEkle.update_json_file("Beam Lenght",self.entry_degeri)

            self.fonksiyon("kiris uzunluk",0)#Ekranı Günceller

class DropDownPanel(Panel):
    def __init__(self, parent, data_vars, options,text, shared_vars,fonksiyon):
        super().__init__(parent=parent)
        self.text=text
        self.shared_vars = shared_vars

        # YAZI
        self.label = ctk.CTkLabel(master=self, text=text, font=('Arial', 15))
        self.label.pack(anchor='w', padx=4, pady=4)

        # SEÇİM
        self.option_menu = ctk.CTkOptionMenu(
            self,
            values=options,
            fg_color=ENTRY_COLOR,
            button_color=DROPDOWN_BUTTON_COLOR,
            button_hover_color=DROPDOWN_HOVER_COLOR,
            dropdown_fg_color=DROPDOWN_MENU_COLOR,
            variable=data_vars,
            command= lambda value: self.birimi_degistir(self.shared_vars, value,fonksiyon) 
        )
        self.option_menu.pack(side='left', fill='x', expand=True, padx=4, pady=4)

        self.pack(fill='x', pady=4, padx=4)

    #oluşan birimi değiştiriyor
    def birimi_degistir(self,shared_vars, value,fonksiyon):
        self.fonksiyon = fonksiyon
        if self.text == TEXT_09:

            JsonEkle.update_json_file("Length Unit",value) #veriyi jsona kaydetti kaydetme
            len_unit_value= BirimiDegistir(value,"0").degistir()
            shared_vars[0].set(len_unit_value)
            #ResimKirisUzunluk(JsonEkle.bilgi_oku("Beam Lenght"),"Kiriş_Uzunluk",self.fonksiyon)
            self.fonksiyon("ekran_veri_yenile",0)#Resmi Günceller
            

        if self.text == TEXT_10:
            JsonEkle.update_json_file("Force Unit",value)  #veriyi jsona kaydetti kaydetme
            force_unit_value = BirimiDegistir(value,"0").degistir()
            shared_vars[1].set(force_unit_value)
        
        #Force Unit'i data.jsonda değiştirir.
        moment_unit_value= "("+ BirimiDegistir((JsonEkle.bilgi_oku("Force Unit")),"1").degistir() +BirimiDegistir((JsonEkle.bilgi_oku("Length Unit")),"1").degistir()+ ")"
        JsonEkle.update_json_file("Moment Unit",moment_unit_value)
        shared_vars[2].set(moment_unit_value)

        #Load Magnitude Unit'i data.jsonda değiştirir.
        load_magnitude_unit_value= "("+BirimiDegistir((JsonEkle.bilgi_oku("Force Unit")),"1").degistir()+"/"+BirimiDegistir((JsonEkle.bilgi_oku("Length Unit")),"1").degistir()+")"
        JsonEkle.update_json_file("Load Magnitude Unit",load_magnitude_unit_value)
        shared_vars[3].set(load_magnitude_unit_value)      

class SupportsSelections(Panel):
    def __init__(self, parent, info, fonksiyon,shared_vars):
        super().__init__(parent=parent)

        self.parent = parent
        self.info = info
        self.fonksiyon = fonksiyon
        self.buton_basınc = 0
        self.shared_var_lenght_unit = shared_vars[0]
        self.labels = []  # Label nesnelerini saklamak için liste

        # Frame'i 3 eşit frame'e böldük
        self.columnconfigure((0, 1, 2), weight=1)
        self.rowconfigure((0, 1, 2, 3), weight=1)

        self.radio_buttons = []

        def select_option(index):
            global selected_option
            selected_option = index
            self.secilen_deger = index
            update_buttons()
            self.update_label(index)

        def update_buttons(): #buton üzerine gelince ve tıklayınca renginin değişmesi
            for i, btn in enumerate(buttons):
                if i == selected_option:
                    btn.configure(fg_color=("gray", "darkgray"))
                    self.radyobutonları(i)
                else:
                    btn.configure(fg_color=("transparent"))

        image_paths = [DosyaKonumu().dosya_konumunu_al("pin_showing"),DosyaKonumu().dosya_konumunu_al("roller_showing"),DosyaKonumu().dosya_konumunu_al("fix_showing"),]
        images = []

        for path in image_paths:
            image = Image.open(path)
            image = image.resize((80, 60))
            images.append(CTkImage(light_image=image, dark_image=image, size=(80, 60)))

        buttons = []
        for i, image in enumerate(images):
            btn = ctk.CTkButton(
                self,
                image=image,
                text="",
                width=80,
                height=60,
                command=lambda i=i: select_option(i),
                hover=False,
                fg_color="transparent",
            )
            btn.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
            buttons.append(btn)

    def radyobutonları(self, i):
        for rb in self.radio_buttons:
            rb.destroy()
        self.radio_buttons.clear()

        if hasattr(self, "label"):
            self.label.destroy()

        # Add a pin Support gibi labellerin yazılı olduğu yer
        self.label_frame = ctk.CTkFrame(master=self, fg_color="transparent")
        self.label_frame.grid(row=1, column=0, columnspan=3, sticky="w")

        if i == 0:
            self.label = ctk.CTkLabel(master=self.label_frame, text=TEXT_11, font=("Arial", 18, "bold"))
        elif i == 1:
            self.label = ctk.CTkLabel(master=self.label_frame, text=TEXT_12, font=("Arial", 18, "bold"))
        elif i == 2:
            self.label = ctk.CTkLabel(master=self.label_frame, text=TEXT_13, font=("Arial", 18, "bold")) 

        self.label.pack(side="left", anchor="w", padx=4, pady=4)


        self.selected_option = ctk.StringVar(value=TEXT_14)  # İlk açıldığında "On the left" seçili olarak gösterir.

        self.radio_frame = ctk.CTkFrame(master=self, fg_color="transparent")
        self.radio_frame.grid(row=2, column=0, sticky="nw")

        self.radiobutton1 = ctk.CTkRadioButton(
            self.radio_frame,
            text=TEXT_14,
            value=TEXT_14,
            variable=self.selected_option,
            command=lambda: self.update_label(selected_option),
        )
        self.radiobutton2 = ctk.CTkRadioButton(
            self.radio_frame,
            text=TEXT_15,
            value=TEXT_15,
            variable=self.selected_option,
            command=lambda: self.update_label(selected_option),
        )

        self.radiobutton1.pack(anchor="n", padx=4, pady=4, side="top")
        self.radiobutton2.pack(anchor="n", padx=4, pady=4, side="top")

        self.radio_buttons.extend([self.radiobutton1, self.radiobutton2])
    
        # "Add" ve "Cancel" butonlarının eklenmesi, "Fixed Support" seçildiğinde de çalışmalı
        if i != 2: 
            self.radiobutton3 = ctk.CTkRadioButton(
                self.radio_frame,
                text=f" {TEXT_24} {(self.shared_var_lenght_unit.get())}",
                value= TEXT_24,
                variable=self.selected_option,
                command=lambda: self.update_label(selected_option),
            )
            self.radiobutton3.pack(anchor="n", padx=4, pady=4, side="top")
            self.radio_buttons.append(self.radiobutton3)

        self.ortak_frame = ctk.CTkFrame(master=self, fg_color="transparent")
        self.ortak_frame.grid(row=3, column=0, columnspan=3, sticky="nswe", padx=4, pady=4) 

        button_add= ctk.CTkButton(master=self.ortak_frame, 
                                text=TEXT_23, 
                                width=125,
                                command= lambda: self.supportsbilgileryolla(), 
                                fg_color=SLIDER_BG,
                                hover_color=GREEN)
        button_add.pack(side="right",padx=2)

        button_cancel= ctk.CTkButton(master=self.ortak_frame, 
                                    text=TEXT_22,
                                    width=85,
                                    command= lambda: self.reset_ui(),
                                    fg_color=SLIDER_BG,
                                    hover_color=CLOSE_RED)
        button_cancel.pack(side="right")

    def supportsbilgileryolla(self):

        if (hasattr(self, "entry5") and self.entry5.get()):
            entry_degeri =self.entry5.get()

            if self.kirisuzunlukkontrol(entry_degeri): #girilen değerin kiriş uzunluğunun içinde olup olmadığına bakıyor

                JsonEkle.Supports_ekle(self,self.button_texts[selected_option],str(self.selected_option.get()),float(self.entry_degeri_checked))# veriyi jsona yazar
                #ResimKirisUzunluk(JsonEkle.bilgi_oku("Beam Lenght"),"supportslar",self.fonksiyon) #Resmi Günceller
                self.fonksiyon("reset_menu","1")
           
        if (self.selected_option.get()==TEXT_14 or str(self.selected_option.get()) == TEXT_15):
            
            if self.selected_option.get()==TEXT_14:
                self.selected_option_checked = "On The Left"
            if self.selected_option.get()==TEXT_15:
                self.selected_option_checked = "On The Right"

            if str(self.selected_option.get()) == TEXT_14:
                self.entry_degeri_checked = 0
            if str(self.selected_option.get()) == TEXT_15:
                self.entry_degeri_checked = float(JsonEkle.bilgi_oku("Beam Lenght"))
                 
            JsonEkle.Supports_ekle(self,self.button_texts[selected_option],str(self.selected_option_checked),self.entry_degeri_checked)# veriyi jsona yazar
            #ResimKirisUzunluk(JsonEkle.bilgi_oku("Beam Lenght"),"supportslar",self.fonksiyon) #Resmi Günceller
            self.fonksiyon("reset_menu","1")


    def reset_ui(self):
        # Resimli butonlar haricinde tüm bileşenleri temizle
        for widget in self.winfo_children():
            if isinstance(widget, ctk.CTkButton):
                widget.configure(fg_color="transparent")  # Butonların rengini sıfırla
                continue
            widget.destroy()

        # Seçili durumu sıfırla
        global selected_option
        selected_option = None
        self.secilen_deger = None

        # UI bileşenlerini ilk haline getir
        self.radio_buttons.clear()



    def update_label(self, index):
        self.button_texts = ["pin", "roller", "fixed"]

        if str(self.selected_option.get()) == TEXT_24:
            self.position_entry()
        else:
            self.remove_position_entry()

    def position_entry(self):
        if not hasattr(self, "entry5"):
            self.entry5 = ctk.CTkEntry(self.ortak_frame,width=120)
            self.entry5.pack(side="left", fill="x", expand=False,padx=2)

    def remove_position_entry(self):
        if hasattr(self, "entry5"):
            self.entry5.destroy()
            del self.entry5

    def kirisuzunlukkontrol(self,entry_degeri):

        self.entry_degeri_checked = entry_degeri
        
        if "," in entry_degeri:
            self.entry_degeri_checked = entry_degeri.replace(",", ".")

        if ( self.entry_degeri_checked.count('.') > 1):
            return False
        
        if not ( self.entry_degeri_checked.replace('.', '').isdigit()):
            return False

        if float(self.entry_degeri_checked)<=float(JsonEkle.bilgi_oku("Beam Lenght")) and float(self.entry_degeri_checked)>=0:
            return True
        else:
            Uyari(TEXT_38, TEXT_34)
            return False

class LoadsSelections(Panel):
    def __init__(self, parent, info, fonksiyon,shared_vars):
        super().__init__(parent=parent)
        self.parent = parent
        self.info = info
        self.fonksiyon = fonksiyon
        self.buton_basınc = 0
        self.shared_var_lenght_unit = shared_vars[0]
        self.shared_var_force_unit = shared_vars[1]
        self.shared_vars=shared_vars
        self.labels = []  # Label nesnelerini saklamak için liste
        # Frame'i 3 eşit frame'e böldük
        self.columnconfigure((0, 1, 2), weight=1)
        self.rowconfigure((0, 1, 2, 3), weight=1)

        self.radio_buttons = []

        def select_option(index):
            global selected_option
            selected_option = index
            self.secilen_deger = index
            update_buttons()

        def update_buttons(): #buton üzerine gelince ve tıklayınca renginin değişmesi
            for i, btn in enumerate(buttons):
                if i == selected_option:
                    btn.configure(fg_color=("gray", "darkgray"))
                    self.radyobutonları(i)
                else:
                    btn.configure(fg_color=("transparent"))

        image_paths = [
            DosyaKonumu().dosya_konumunu_al("point_showing"),
            DosyaKonumu().dosya_konumunu_al("moment_showing"),
            DosyaKonumu().dosya_konumunu_al("distload_showing"),
        ]
        images = []

        for path in image_paths:
            image = Image.open(path)
            image = image.resize((80, 60))
            images.append(CTkImage(light_image=image, dark_image=image, size=(80, 60)))

        buttons = []
        for i, image in enumerate(images):
            btn = ctk.CTkButton(
                self,
                image=image,
                text="",
                width=80,
                height=60,
                command=lambda i=i: select_option(i),
                hover=False,
                fg_color="transparent",
            )
            btn.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
            buttons.append(btn)

    def radyobutonları(self, i):

        self.secili_loads = i
        for rb in self.radio_buttons:
            rb.destroy()
        self.radio_buttons.clear()

        if hasattr(self, "label"):
            self.label.destroy()

        self.label_frame = ctk.CTkFrame(master=self, fg_color="transparent")
        self.label_frame.grid(row=1, column=0, columnspan=3, sticky="w")

        if i == 0:
            self.label = ctk.CTkLabel(
            master=self.label_frame, text=TEXT_17, font=("Arial", 18, "bold")
            )
        elif i == 1:
            self.label = ctk.CTkLabel(
                master=self.label_frame, text=TEXT_18, font=("Arial", 18, "bold")
            )
        elif i == 2:
            self.label = ctk.CTkLabel(
                master=self.label_frame, text=TEXT_19, font=("Arial", 18, "bold")
            )   

        self.label.pack(side="left", anchor="w", padx=4, pady=4)

        self.selected_option = ctk.StringVar(value=TEXT_14)  # İlk açıldığında seçili olarak gösterir.

        self.radio_frame = ctk.CTkFrame(master=self, fg_color="transparent")
        self.radio_frame.grid( column=0, columnspan=3, sticky="nswe")      

        if i ==0:
            self.positions_entry =EntryPanel(self.radio_frame,TEXT_24, self.shared_vars,self.fonksiyon)
            self.load_entry = EntryPanel(self.radio_frame,TEXT_25, self.shared_vars,self.fonksiyon)
            self.angle_entry = EntryPanel(self.radio_frame,TEXT_26, self.shared_vars,self.fonksiyon)

        if i ==1:
            self.positions_entry_bending= EntryPanel(self.radio_frame,TEXT_24, self.shared_vars,self.fonksiyon)
            self.moment_entry_bending= EntryPanel(self.radio_frame,TEXT_27, self.shared_vars,self.fonksiyon) 

        if i ==2:
            self.distload_start_position_entry=EntryPanel(self.radio_frame,TEXT_28, self.shared_vars,self.fonksiyon)
            self.distload_end_position_entry=EntryPanel(self.radio_frame,TEXT_29, self.shared_vars,self.fonksiyon) 
            self.distload_load_entry=EntryPanel(self.radio_frame,TEXT_30, self.shared_vars,self.fonksiyon) 

        self.radio_buttons.append(self.radio_frame)

        self.ortak_frame = ctk.CTkFrame(master=self, fg_color="transparent")
        self.ortak_frame.grid(row=3, column=0, columnspan=3, sticky="nswe", padx=4, pady=4) 

        button_add= ctk.CTkButton(master=self.ortak_frame, 
                                text=TEXT_23, 
                                width=125,
                                command= lambda: self.bilgilerkontrolu(secili_loads=self.secili_loads), 
                                fg_color=SLIDER_BG,
                                hover_color=GREEN)
        button_add.pack(side="right",padx=2)

        button_cancel= ctk.CTkButton(master=self.ortak_frame, 
                                    text=TEXT_22,
                                    width=85,
                                    command= lambda: self.reset_ui(),
                                    fg_color=SLIDER_BG,
                                    hover_color=CLOSE_RED)
        button_cancel.pack(side="right")

        self.radio_buttons.append(self.ortak_frame)


    def bilgilerkontrolu(self,secili_loads): # ekrana girilen değerlerin doğru mu veya yanlış mı olduğuna bakıyor ve duruma göre True veya False gönderiyor.

        kiris_uzunluk = float(JsonEkle.bilgi_oku("Beam Lenght")) 

        if secili_loads==0:#Point Load

            self.positions_entry.entry_EntryPanel_value = self.positions_entry.entry_EntryPanel.get()
            self.load_entry.entry_EntryPanel_value = self.load_entry.entry_EntryPanel.get()
            self.angle_entry.entry_EntryPanel_value = self.angle_entry.entry_EntryPanel.get()

            #Girilen değerlerde eğer virgül varsa noktaya çeviriyor
            if "," in self.positions_entry.entry_EntryPanel_value:
                self.positions_entry.entry_EntryPanel_value = self.positions_entry.entry_EntryPanel_value.replace(",", ".")
            if "," in self.load_entry.entry_EntryPanel_value:
                self.load_entry.entry_EntryPanel_value = self.load_entry.entry_EntryPanel_value.replace(",", ".")
            if "," in self.angle_entry.entry_EntryPanel_value:
                self.angle_entry.entry_EntryPanel_value = self.angle_entry.entry_EntryPanel_value.replace(",", ".")
            
            #Girilen değerlerde yanlış veya eksik birşey varsa program devam etmiyor.
            if self.girilen_sayi_kontrol(self.positions_entry.entry_EntryPanel_value,TEXT_24)== False:
                return False
            if self.girilen_sayi_kontrol(self.load_entry.entry_EntryPanel_value,"load")== False:
                return False
            
            #Girilen değerlerin kiriş aralığında ve istenilen açı değeri aralığında olup olmadığını kontrol ediyor.
            if not (float(self.positions_entry.entry_EntryPanel_value)<=kiris_uzunluk and float(self.positions_entry.entry_EntryPanel_value)>= 0):
                return False           
            if float(self.angle_entry.entry_EntryPanel_value)>180 or float(self.angle_entry.entry_EntryPanel_value)<0:
                Uyari(TEXT_39,TEXT_34)
                return False
            
            else:
                self.jsonloadsyolla(self.secili_loads)
                self.reset_ui()
                #ResimKirisUzunluk(JsonEkle.bilgi_oku("Beam Lenght"),"loadslar",self.fonksiyon)#Resmi Günceller
                self.fonksiyon("reset_menu","2")

        if secili_loads==1:#Bending Moment

            self.positions_entry_bending.entry_EntryPanel_value = self.positions_entry_bending.entry_EntryPanel.get()
            self.moment_entry_bending.entry_EntryPanel_value = self.moment_entry_bending.entry_EntryPanel.get()

            #Girilen değerlerde eğer virgül varsa noktaya çeviriyor
            if "," in self.positions_entry_bending.entry_EntryPanel_value:
                self.positions_entry_bending.entry_EntryPanel_value = self.positions_entry_bending.entry_EntryPanel_value.replace(",", ".")
            if "," in self.moment_entry_bending.entry_EntryPanel_value:
                self.moment_entry_bending.entry_EntryPanel_value = self.moment_entry_bending.entry_EntryPanel_value.replace(",", ".")
            
            #Girilen değerlerde yanlış veya eksik birşey varsa program devam etmiyor.
            if self.girilen_sayi_kontrol(self.positions_entry_bending.entry_EntryPanel_value,TEXT_24)== False:
                return False        
            if self.girilen_sayi_kontrol(self.moment_entry_bending.entry_EntryPanel_value,"load")== False:
                return False
            
            #Girilen değerlerin kiriş aralığında olup olmadığını kontrol ediyor.
            if not (float(self.positions_entry_bending.entry_EntryPanel_value)<=kiris_uzunluk and float(self.positions_entry_bending.entry_EntryPanel_value)>= 0):
                return False 
            
            else:
                self.jsonloadsyolla(self.secili_loads)
                self.reset_ui()
                #ResimKirisUzunluk(JsonEkle.bilgi_oku("Beam Lenght"),"loadslar",self.fonksiyon)#Resmi Günceller
                self.fonksiyon("reset_menu","2")

        if secili_loads == 2:#Düzgün Yayılı Yük

            self.distload_start_position_entry.entry_EntryPanel_value = self.distload_start_position_entry.entry_EntryPanel.get()
            self.distload_end_position_entry.entry_EntryPanel_value = self.distload_end_position_entry.entry_EntryPanel.get()
            self.distload_load_entry.entry_EntryPanel_value = self.distload_load_entry.entry_EntryPanel.get()

            #Girilen değerlerde eğer virgül varsa noktaya çeviriyor
            if "," in self.distload_start_position_entry.entry_EntryPanel_value:
                self.distload_start_position_entry.entry_EntryPanel_value = self.distload_start_position_entry.entry_EntryPanel_value.replace(",", ".")
            if "," in self.distload_end_position_entry.entry_EntryPanel_value:
                self.distload_end_position_entry.entry_EntryPanel_value = self.distload_end_position_entry.entry_EntryPanel_value.replace(",", ".")
            if "," in self.distload_load_entry.entry_EntryPanel_value:
                self.distload_load_entry.entry_EntryPanel_value = self.distload_load_entry.entry_EntryPanel_value.replace(",", ".")
           
            #Girilen değerlerde yanlış veya eksik birşey varsa program devam etmiyor.
            if self.girilen_sayi_kontrol(self.distload_start_position_entry.entry_EntryPanel_value,TEXT_24)== False:
                return False
            if self.girilen_sayi_kontrol(self.distload_end_position_entry.entry_EntryPanel_value,TEXT_24)== False:
                return False
            if self.girilen_sayi_kontrol(self.distload_load_entry.entry_EntryPanel_value,"load")== False:
                return False

            #Girilen değerlerin kiriş aralığında olup olmadığını kontrol ediyor.
            if (float(self.distload_start_position_entry.entry_EntryPanel_value)>kiris_uzunluk) or (float(self.distload_start_position_entry.entry_EntryPanel_value)<0):
                Uyari(TEXT_38, TEXT_34)
                return False   
            if (float(self.distload_end_position_entry.entry_EntryPanel_value)>kiris_uzunluk) or (float(self.distload_end_position_entry.entry_EntryPanel_value)<0):
                Uyari(TEXT_38, TEXT_34)
                return False       
            if (float(self.distload_end_position_entry.entry_EntryPanel_value)<=float(self.distload_start_position_entry.entry_EntryPanel_value)):
                Uyari(TEXT_40, TEXT_34)
                return False
            
            else:
                self.jsonloadsyolla(self.secili_loads)
                self.reset_ui()
                #ResimKirisUzunluk(JsonEkle.bilgi_oku("Beam Lenght"),"loadslar",self.fonksiyon)       
                self.fonksiyon("reset_menu","2")                   

    def girilen_sayi_kontrol(self,sayi:str,info:str): #sayıların içinde istenmeyen karakterlerin olup olmadığını kontrol ediyor.
        self.sayi = sayi

        #sayıların içinde istenmeyen karakterlerin olup olmadığını kontrol ediyor.
        if info=="load":
            if all(c.isdigit() or c in [".","-"] for c in self.sayi):
                if self.sayi.count(".") <=1 and self.sayi.count("-")<=1:
                    if "-" in self.sayi and self.sayi.index("-") !=0:
                        return False
                    else:
                        return True
                else:
                    return False
            else:
                return False 
        elif info ==TEXT_24:

            if all(c.isdigit() or c in ["."] for c in self.sayi):

                if self.sayi.count(".") <=1:
                    return True
                else:
                    return False
            else:
                return False

    def jsonloadsyolla(self,secili_loads): # Ekrana girilen doğru bilgileri jsona gönderiyor.

        load= []
        if secili_loads ==0:#Point Load
            load.append("Point Load")
            load.append(float(self.positions_entry.entry_EntryPanel_value))
            load.append(float(self.load_entry.entry_EntryPanel_value))
            load.append(float(self.angle_entry.entry_EntryPanel_value))

        if secili_loads ==1:#Bending Moment
            load.append("Bending Moment")
            load.append(float(self.positions_entry_bending.entry_EntryPanel_value))
            load.append(float(self.moment_entry_bending.entry_EntryPanel_value))
            
        if secili_loads ==2:#Düzgün Yayılı Yük
            load.append("Distributed Load")
            load.append(float(self.distload_start_position_entry.entry_EntryPanel_value))
            load.append(float(self.distload_end_position_entry.entry_EntryPanel_value))
            load.append(float(self.distload_load_entry.entry_EntryPanel_value))

        #jsonloadssekle(load)
        JsonEkle.loads_ekle(load)


    def reset_ui(self): #Add veya Cancel butonuna bastığında ekrandaki radioframe gibi widgetleri kapatıyor.
        # Resimli butonlar haricinde tüm bileşenleri temizle
        for widget in self.winfo_children():
            if isinstance(widget, ctk.CTkButton):
                widget.configure(fg_color="transparent")  # Butonların rengini sıfırla
                continue
            widget.destroy()

        # Seçili durumu sıfırla
        global selected_option
        selected_option = None
        self.secilen_deger = None

        # UI bileşenlerini ilk haline getir
        self.radio_buttons.clear()

class SupportsData(Panel):
    def __init__(self, parent, liste,fonksiyon,shared_vars):
        super().__init__(parent=parent)
        self.liste = liste  # ["mesafe", "support tipi"]
        self.fonksiyon = fonksiyon
        self.shared_var_lenght_unit = shared_vars[0]
        self.shared_var_beam_lenght = shared_vars[4]

        #SupportsBilgiler.support_bilgiler = JsonEkle.bilgi_oku("Supports")

        self.label = ctk.CTkLabel(master=self, text=TEXT_03, font=("Helvetica", 25, "bold"))
        self.label.pack(anchor="w", padx=4, pady=4)

        if len(self.liste) == 0:#Supports Yok ise listeye There İs No Support Ekliyecek.
            self.liste = [[TEXT_20, "", ""]]

        for supportlar in self.liste:
            self.info_frame = ctk.CTkFrame(master=self, fg_color='transparent')
            self.info_frame.pack(fill='x')

            if supportlar[-1] != "":
                self.label1 = ctk.CTkLabel(master=self.info_frame, text=f"{supportlar[0].capitalize()} Support : ", font=('Arial', 15))
                self.label1.pack(side="left", pady=2,padx=5)

                self.middle_frame = ctk.CTkFrame(master=self.info_frame,fg_color=DARK_GREY)  # Orta frame oluşturuluyor
                self.middle_frame.pack(side="left", expand=True)  # Orta frame'i yerleştir, genişlesin

                # Label2 ve Label3 (Orta)
                if supportlar[1] == TEXT_15:
                    self.label2 = ctk.CTkLabel(master=self.middle_frame, textvariable=self.shared_var_beam_lenght, font=('Arial', 15))
                else:
                    self.label2 = ctk.CTkLabel(master=self.middle_frame, text=supportlar[2], font=('Arial', 15))

                self.label2.pack(side="left", pady=2,)

                self.label3 = ctk.CTkLabel(master=self.middle_frame, textvariable=self.shared_var_lenght_unit, font=('Arial', 15))
                self.label3.pack(side="left", pady=2, padx=2)

                # Silme Butonu
                silme_butonu = ctk.CTkButton(master=self.info_frame, text="X", width=50, command=lambda s=supportlar: self.silme_butonu(s), fg_color=SLIDER_BG,hover_color=CLOSE_RED)
                silme_butonu.pack(side="right", padx=10)



            else: #supports yok ise There is no supports yazacak
                self.label1 = ctk.CTkLabel(master=self.info_frame, text=f"{supportlar[0]}", font=('Arial', 15))
                self.label1.pack(side="left", pady=2,padx=5)


    def silme_butonu(self, text): # silme butonuna basıldığında Supportu Siler

        JsonEkle.bilgi_sil("Supports",text) #veriyi jsondan siler 
        #ResimKirisUzunluk(JsonEkle.bilgi_oku("Beam Lenght"),"supportslar",self.fonksiyon)
        self.fonksiyon("reset_menu","1")

class LoadsData(Panel):
    def __init__(self, parent, liste,fonksiyon,shared_vars):
        super().__init__(parent=parent)
        self.liste = liste  # [["Load tipi", uzaklık, vs...]]
        self.fonksiyon = fonksiyon
        self.shared_var_lenght_unit = shared_vars[0]
        self.shared_var_force_unit = shared_vars[1]
        self.shared_var_moment_unit = shared_vars[2]
        self.shared_var_load_mangnitude_unit = shared_vars[3]
        self.shared_var_beam_lenght = shared_vars[4]

        self.label = ctk.CTkLabel(master=self, text="Loads", font=("Helvetica", 25, "bold"))
        self.label.pack(anchor="w", padx=4, pady=4)

        if len(self.liste) == 0:
            self.liste = [[TEXT_21, "", ""]]
        for loadlar in self.liste:
            self.info_frame = ctk.CTkFrame(master=self, fg_color='transparent')
            self.info_frame.pack(fill='x',pady=5)

            if loadlar[-1] == "":
                self.label1 = ctk.CTkLabel(master=self.info_frame, text=f"{loadlar[0]}", font=('Arial', 15))
                self.label1.pack(side="left", pady=2,padx=5)
            else:

                if loadlar[0]=="Point Load":
                    self.label1 = ctk.CTkLabel(master=self.info_frame, text=f"{loadlar[0].capitalize()}, {loadlar[1]}", font=('Arial', 15))
                    self.label1.pack(side="left", pady=2,padx=5)

                    self.label2 = ctk.CTkLabel(master=self.info_frame, textvariable=(self.shared_var_lenght_unit), font=('Arial', 15))
                    self.label2.pack(side="left", pady=2)

                    self.label3 = ctk.CTkLabel(master=self.info_frame, text=f" , {loadlar[2]} ", font=('Arial', 15))
                    self.label3.pack(side="left", pady=2)

                    self.label4 = ctk.CTkLabel(master=self.info_frame, textvariable=self.shared_var_force_unit, font=('Arial', 15))
                    self.label4.pack(side="left", pady=2)

                    self.label5 = ctk.CTkLabel(master=self.info_frame, text=f" , {loadlar[3]} deg", font=('Arial', 15))
                    self.label5.pack(side="left", pady=2)

                elif loadlar[0]=="Bending Moment":
                    self.label1 = ctk.CTkLabel(master=self.info_frame, text=f"{loadlar[0].capitalize()}, {loadlar[1]}", font=('Arial', 15))
                    self.label1.pack(side="left", pady=2,padx=5)

                    self.label2 = ctk.CTkLabel(master=self.info_frame, textvariable=self.shared_var_lenght_unit, font=('Arial', 15))
                    self.label2.pack(side="left", pady=2)

                    self.label3 = ctk.CTkLabel(master=self.info_frame, text=f" , {loadlar[2]} ", font=('Arial', 15))
                    self.label3.pack(side="left", pady=2)

                    self.label4 = ctk.CTkLabel(master=self.info_frame, textvariable=self.shared_var_moment_unit, font=('Arial', 15))
                    self.label4.pack(side="left", pady=2)

                elif loadlar[0]=="Distributed Load":
                    self.label1 = ctk.CTkLabel(master=self.info_frame, text=f"{loadlar[0].capitalize()}, {loadlar[1]} to {loadlar[2]}", font=('Arial', 15))
                    self.label1.pack(side="left", pady=2,padx=5)

                    self.label2 = ctk.CTkLabel(master=self.info_frame, textvariable=self.shared_var_lenght_unit, font=('Arial', 15))
                    self.label2.pack(side="left", pady=2)

                    self.label3 = ctk.CTkLabel(master=self.info_frame, text=f" , {loadlar[3]} ", font=('Arial', 15))
                    self.label3.pack(side="left", pady=2)

                    self.label4 = ctk.CTkLabel(master=self.info_frame, textvariable=self.shared_var_load_mangnitude_unit, font=('Arial', 15))
                    self.label4.pack(side="left", pady=2)

                silme_butonu = ctk.CTkButton(master=self.info_frame, text="X", width=50,command=lambda s=loadlar: self.silme_butonu(s), fg_color=SLIDER_BG,hover_color=CLOSE_RED)
                silme_butonu.pack(side="right", padx=10)

    def silme_butonu(self, silinecek): # silme butonuna basıldığında Loadsı Siler
        JsonEkle.bilgi_sil("Loads",silinecek)
        #ResimKirisUzunluk(JsonEkle.bilgi_oku("Beam Lenght"),"loadslar",self.fonksiyon)
        self.fonksiyon("reset_menu","2")

class Button(ctk.CTkButton):#Basıldığı Zaman Fonksiyon Çalıştıran Buton.
    def __init__(self, parent, func,text):
        super().__init__(master=parent, text=text, command=self.sonrakineggit)
        self.pack(side="bottom", pady=10)
        self.func = func

    def sonrakineggit(self):
        self.func()
    
class ToggleButton(ctk.CTkFrame):
    def __init__(self, parent, liste, shared_vars,fonksiyon):
        super().__init__(parent, fg_color=DARK_GREY)
        self.parent = parent

        self.shared_var_moment_of_inertia_lenght = shared_vars[7]
        self.shared_var_youngs_module_lenght = shared_vars[8]
        self.shared_var_force_unit = shared_vars[1]
        self.shared_vars = shared_vars
        self.fonksiyon=fonksiyon

        # Ekstra çerçeve (frame) ve label için
        self.extra_frame = ctk.CTkFrame(self,fg_color=DARK_GREY)

        self.label_frame = ctk.CTkFrame(master=self.extra_frame, fg_color="transparent")
        self.label_frame.pack(fill='x',padx=4)

        self.entry_frame = ctk.CTkFrame(master=self.extra_frame, fg_color="transparent")
        self.entry_frame.pack(fill='x',padx=4)

        # "Moment Of Inertia" yazısı Label
        self.label = ctk.CTkLabel(master=self.label_frame, text=TEXT_52, font=('Arial', 15))
        self.label.pack(side='left', anchor='w', padx=4)

        # Birim Gösteren Label
        self.meter_label = ctk.CTkLabel(master=self.label_frame, text="(mm^4)", font=('Arial', 12))
        self.meter_label.pack(side='left', anchor='w', padx=0)
        # Entry
        self.entry_EntryPanel = ctk.CTkEntry(self.entry_frame)
        self.entry_EntryPanel.pack(side='left', fill='x', expand=True, padx=4,ipady=1)

        self.entry_EntryPanel.insert(0, JsonEkle.bilgi_oku("Moment Of Inertia"))
        self.entry_EntryPanel.bind("<FocusOut>", self.on_focus_out_moment_of_inertia)
        self.entry_EntryPanel.bind("<KeyRelease>", self.on_focus_out_moment_of_inertia)

        self.label_frame2 = ctk.CTkFrame(master=self.extra_frame, fg_color="transparent")
        self.label_frame2.pack(fill='x',padx=4,pady=4)

        self.entry_frame2 = ctk.CTkFrame(master=self.extra_frame, fg_color="transparent")
        self.entry_frame2.pack(fill='x',padx=4,pady=4)

        # "Young's Module" yazısı Label
        self.label2 = ctk.CTkLabel(master=self.label_frame2, text=TEXT_53, font=('Arial', 15))
        self.label2.pack(side='left', anchor='w', padx=4)
        # Birim Gösteren Label
        self.meter_label2 = ctk.CTkLabel(master=self.label_frame2, text="(N/mm2)", font=('Arial', 12))
        self.meter_label2.pack(side='left', anchor='w', padx=0)
        # Entry
        self.entry_EntryPanel2 = ctk.CTkEntry(self.entry_frame2)
        self.entry_EntryPanel2.pack(side='left', fill='x', expand=True, padx=4,ipady=1)

        self.entry_EntryPanel2.insert(0, JsonEkle.bilgi_oku("Young's Module"))
        self.entry_EntryPanel2.bind("<FocusOut>", self.on_focus_out_youngs_module)
        self.entry_EntryPanel2.bind("<KeyRelease>", self.on_focus_out_youngs_module)


        # Çerçevenin tüm sütunlarını tam genişlikte yaymak için
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)
        
        # Listeyi döngüyle işleyip her eleman için buton ve yazıyı yan yana oluşturuyoruz
        for i, eleman in enumerate(liste):
            text = eleman[0]
            durum = eleman[1]

            if text == "Bending Moment Diagram (BMD)":
                text_label = f"{TEXT_41} ({TEXT_43})"

            if text == "Shear Force Diagram (SFD)":
                text_label = f"{TEXT_45} ({TEXT_47})"

            if text == "Deflection Diagram":
                text_label = TEXT_48

            self.create_button(text, durum, i,text_label)

        self.pack(fill='x', pady=10, padx=4)

    def on_focus_out_moment_of_inertia(self, event):
       JsonEkle.update_json_file("Moment Of Inertia",int(self.entry_EntryPanel.get()))

    def on_focus_out_youngs_module(self, event):
       JsonEkle.update_json_file("Young's Module",int(self.entry_EntryPanel2.get()))




    def create_button(self, text, durum, row,text_label):
        # Kapalı ve açık durumlarını kontrol eden fonksiyonlar
        def kapat(togglephoto, togglebutton):
            togglephoto.configure(file=DosyaKonumu().dosya_konumunu_al("off_button"))
            togglebutton.configure(command=lambda: ac(togglephoto, togglebutton))
            JsonEkle.bilgi_sil("Hesaplanmasi istenenler",text)
            self.extra_frame.grid_forget()  # Frame'i gizle

        def ac(togglephoto, togglebutton):
            togglephoto.configure(file=DosyaKonumu().dosya_konumunu_al("on_button"))
            togglebutton.configure(command=lambda: kapat(togglephoto, togglebutton))
            JsonEkle.veri_ekle(self,"Hesaplanmasi istenenler",text)
            if text == "Deflection Diagram":
                self.extra_frame.grid(row=row + 1, column=0, columnspan=2, sticky="ew")  # Frame'i göster

        # Label (Yazı)
        yazi = ctk.CTkLabel(self, text=text_label, font=("Helvetica", 15))
        yazi.grid(row=row, column=0, padx=5, pady=5, sticky="w")  # Sola yaslı

        # Durum kontrolü
        if durum == "Açık":
            togglephoto = tk.PhotoImage(file=DosyaKonumu().dosya_konumunu_al("on_button"))
            togglebutton = tk.Button(self, image=togglephoto, border=0, command=lambda: kapat(togglephoto, togglebutton), bg=DARK_GREY, activebackground=DARK_GREY)
            if text == "Deflection Diagram":
                self.extra_frame.grid(row=row + 1, column=0, columnspan=2, sticky="ew")  # Frame'i göster     
   
        else:  # "Kapalı" durumda
            togglephoto = tk.PhotoImage(file=DosyaKonumu().dosya_konumunu_al("off_button"))
            togglebutton = tk.Button(self, image=togglephoto, border=0, command=lambda: ac(togglephoto, togglebutton), bg=DARK_GREY, activebackground=DARK_GREY)

        # Görüntülemek için butonu ekliyoruz
        togglebutton.image = togglephoto  # Referansı kaybetmemek için image'i saklıyoruz
        togglebutton.grid(row=row, column=1, padx=5, pady=5, sticky="e")  # Sağa yaslı




