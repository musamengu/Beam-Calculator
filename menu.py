import customtkinter as ctk 
from panels import * #Custom Library
from BeamLibrary import * #Custom Library from githup

class Menu(ctk.CTkTabview):

    def __init__(self,parent, shared_vars, fonksiyon, info):
        
        self.parent = parent #Main Classından Gelen Referans
        self.fonksiyon = fonksiyon
        self.info = info
        self.shared_vars = shared_vars

        super().__init__(master = parent)
        self.grid(row=0, column = 0, sticky = 'nsew', pady=10, padx =10) 
        self.bir= self.add(TEXT_02)
        self.iki = self.add(TEXT_03)
        self.uc= self.add(TEXT_04)
        self.dort= self.add(TEXT_05)

        if self.info =="1":
            self.set(TEXT_03)

        if self.info =="2":
            self.set(TEXT_04)

        #widgets
        Length(self.bir, self.shared_vars,self.fonksiyon)
        Destekler(self.iki,fonksiyon,self.shared_vars)  
        Loads(self.uc,fonksiyon,self.shared_vars)
        Calculation(self.dort,fonksiyon,self.shared_vars)

        #Ekrandaki Sonraki Sayfaya Gitmeyi Yönlendiren Ve Analizi Başlatan Butonlar.
        Button(self.tab(TEXT_02),lambda: self.sonrakinegit(TEXT_02),TEXT_31)
        Button(self.tab(TEXT_03),lambda:self.sonrakinegit(TEXT_03),TEXT_32)
        Button(self.tab(TEXT_04), lambda:self.sonrakinegit(TEXT_04),TEXT_33)
        Button(self.tab(TEXT_05), lambda:self.sonrakinegit(TEXT_05),TEXT_01)

    def sonrakinegit(self,text): #Tab'lar Arası Geçiş Ve Analizi Başlatma Görevini İçeriyor.
        if text == TEXT_02:
            pozisyon = TEXT_03
        if text == TEXT_03:
            pozisyon = TEXT_04
        if text == TEXT_04:
            pozisyon=TEXT_05
        if text == TEXT_05:
            if len(JsonEkle.bilgi_oku("Loads"))==0 and len(JsonEkle.bilgi_oku("Supports"))==0: #Load ve Support Yok İse Hata Verir.
                Uyari(TEXT_35,TEXT_34)
            elif len(JsonEkle.bilgi_oku("Loads"))!=0 and len(JsonEkle.bilgi_oku("Supports"))==0: #Support Yok İse Hata Verir.
                Uyari(TEXT_36,TEXT_34)            
            elif len(JsonEkle.bilgi_oku("Loads"))==0 and len(JsonEkle.bilgi_oku("Supports"))!=0: #Load Yok İse Hata Verir.
                Uyari(TEXT_37,TEXT_34) 
            else:
                self.analizi_baslat()

            pozisyon = TEXT_05

        self.set(pozisyon)

    def analizi_baslat(self): #Girilen Verileri BeamLibrary Class'ına gönderip Grafiklerin Ekranda Gözükmesini Sağlıyor.
        
        try:
            elements=[]
            i = 1

            for x in JsonEkle.bilgi_oku("Supports"): #Elements listesine Supportları Ekliyor.

                    if x[0]=='fixed':
                        if x[1]=='On The Left':
                            y = Reaction(0, 'f', f"{i}")
                        if x[1]=='On The Right':
                            y = Reaction(float(JsonEkle.bilgi_oku("Beam Lenght")), 'f', f"{i}")             

                    if x[0]=="roller":
                        if x[1]=='On The Left':
                            y = Reaction(0, 'r', f"{i}")
                        if x[1]=='On The Right':
                            y = Reaction(float(JsonEkle.bilgi_oku("Beam Lenght")), 'r', f"{i}")
                        if x[1]==TEXT_24:
                            y = Reaction(float(x[-1]), 'r', f"{i}")

                    if x[0]=="pin":
                        if x[1]=='On The Left':
                            y = Reaction(0, 'h', f"{i}")
                        if x[1]=='On The Right':
                            y = Reaction(float(JsonEkle.bilgi_oku("Beam Lenght")), 'h', f"{i}")
                        if x[1]==TEXT_24:
                            y = Reaction(float(x[-1]), 'h', f"{i}")
                    
                    i+=1
                    elements.append(y)
            
            for x in JsonEkle.bilgi_oku("Loads"): #Elements Listesine Loads'ları Ekliyor.

                    if x[0]=="Point Load":
                        b = PointLoad(float(x[1]), (float(x[2])*-1),inverted=False,inclination=float(x[-1])) #yukarıdan aşağı= True
                    if x[0]=="Bending Moment":
                        b = PointMoment(float(x[1]),(float(x[2])*-1))
                    if x[0]=="Distributed Load":
                        b = UDL(float(x[1]),float(x[3]),(float(x[2])-float(x[1])))

                    elements.append(b)

            b = Beam(float(JsonEkle.bilgi_oku("Beam Lenght")))
            b.fast_solve(elements)

            gosterilecek_liste = []
            for goster in JsonEkle.bilgi_oku("Hesaplanmasi istenenler"): #Gösterilmesi İstenen Sonuçları Ekliyor.
                if goster == "Bending Moment Diagram (BMD)":
                    data = 'bmd'
                if goster == "Shear Force Diagram (SFD)":
                    data='sfd'
                if goster ==  "Deflection Diagram":
                    data = 'dd' 
                gosterilecek_liste.append(data)

            if len(JsonEkle.bilgi_oku("Hesaplanmasi istenenler"))==1: #Eğer Bir Tane Sonuç Gösterilmek İsteniyorsa O Fonksiyonu Çalıştırıyor.
                b.generate_graph_tek(which=gosterilecek_liste[0],details = True)
            else: #Eğer Birden Fazla Sonuç Gösterilmek İsteniyorsa O Fonksiyonu Çalıştırıyor.
                b.generate_graph_coklu(which=gosterilecek_liste,details=True)

        except:
            Uyari(TEXT_36,TEXT_34)

class Length(ctk.CTkFrame):
    def __init__(self,parent,shared_vars,fonksiyon):
        super().__init__(master= parent, fg_color= 'transparent')
        self.pack(expand = True, fill = 'both')
        EntryPanel(self,TEXT_08,shared_vars,fonksiyon)
        DropDownPanel(self,ctk.StringVar(value= JsonEkle.bilgi_oku("Length Unit")), LENGHT_OPTIONS, TEXT_09, shared_vars,fonksiyon)
        DropDownPanel(self,ctk.StringVar(value= JsonEkle.bilgi_oku("Force Unit")), FORCE_OPTIONS,TEXT_10,shared_vars,fonksiyon)

class Destekler(ctk.CTkFrame):
    def __init__(self, parent, fonksiyon, shared_vars):
        super().__init__(master=parent, fg_color='transparent')
        self.parent = parent #Menu Classından Gelen Referans
        self.pack(expand=True, fill='both')
        SupportsSelections(self, self.info, fonksiyon, shared_vars)
        SupportsData(self, JsonEkle.bilgi_oku("Supports"),fonksiyon,shared_vars)

class Loads(ctk.CTkFrame):
    def __init__(self, parent, fonksiyon, shared_vars):
        super().__init__(master=parent, fg_color='transparent')
        self.parent = parent #Menu Classından Gelen Referans

        self.pack(expand=True, fill='both')
        LoadsSelections(self, self.info, fonksiyon, shared_vars)    
        LoadsData(self, JsonEkle.bilgi_oku("Loads"),fonksiyon,shared_vars)
        
class Calculation(ctk.CTkFrame):
    def __init__(self, parent, fonksiyon, shared_vars):
        super().__init__(master=parent, fg_color='transparent')
        self.parent = parent #Menu Classından Gelen Referans

        self.pack(expand=True, fill='both')

        bmd_situation, sfd_situation, def_situation = "Kapalı", "Kapalı", "Kapalı"


        for liste in JsonEkle.bilgi_oku("Hesaplanmasi istenenler"):
            if liste == "Bending Moment Diagram (BMD)":
                bmd_situation = "Açık"
            if liste == "Shear Force Diagram (SFD)":
                sfd_situation = "Açık"
            if liste == "Deflection Diagram":
                def_situation = "Açık"

        ToggleButton(self,[["Shear Force Diagram (SFD)",bmd_situation],
                            ["Bending Moment Diagram (BMD)",sfd_situation],
                            ],shared_vars,fonksiyon)

        ToggleButton(self,[["Deflection Diagram",def_situation]],shared_vars,fonksiyon)


        