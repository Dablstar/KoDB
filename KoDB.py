from sqlite3 import *
from tkinter import *
from tkinter import ttk
from tkinter.messagebox import *
from tkinter.filedialog import *
import configparser


MAIN_WIDTH = 800
MAIN_HEIGHT = 540
INFO_WIDTH = 340
INFO_HEIGHT = 160
EDITOR_WIDTH = 496
EDITOR_HEIGHT = 360
LOGIN_WIDTH = 300
LOGIN_HEIGHT = 180
SEARCH_WIDTH = 300
SEARCH_HEIGHT = 100


TEXT_INFO = """\
База данных 'Герои СССР'
(c) Копылов Н.А., Москва, 2023
"""

TEXT_MANUAL = """\
База данных Герои СССР
Позволяет: добавлять / удалять / изменять информацию.

Управление:
F1 - вызов справки по программе
F2 - добавить в базу данных
F3 - удалить из базы данных
F4 - изменить запись в базе данных
F10 - меню программы
"""

TEXT_HELP = "F1 - Помощь | F2 - Добавить | F3 - Удалить | F4 - Изменить"


class KoDB:
    fViewInfo: bool
    fViewSearch: bool
    imageBuffer: bytes
    querydata: list
    namelist: list
    cursor: Cursor
    mainForm: Tk
    mainMenu: Menu
    mainCanvas: Canvas
    selectedText: Text
    memberlist: Listbox
    
    def __init__(self):
        self.fViewInfo = False
        self.fViewSearch = False
        self.imageBuffer = None
        self.namelist = []
        self.querydata = []
        
        self.cursor = connect("KoDB.db").cursor()
        self.cursor.execute("CREATE TABLE if not exists table1 (id INTEGER PRIMARY KEY, fio TEXT, item TEXT, image BLOB);")

    def run(self):
        self.logIn()

        mainForm = Tk()
        mainForm.title("Герои СССР")
        mainForm.resizable(height=False, width=False)
        self.mainForm = mainForm

        screen_width = mainForm.winfo_screenwidth()
        screen_height = mainForm.winfo_screenheight()

        x = (screen_width/2) - (MAIN_WIDTH/2)
        y = (screen_height/2) - (MAIN_HEIGHT/2)

        mainForm.geometry('%dx%d+%d+%d' % (MAIN_WIDTH, MAIN_HEIGHT, x, y - 40))

        mainMenu = Menu()
        mainForm.config(menu=mainMenu)
        self.mainMenu = mainMenu

        menu1 = Menu(tearoff=False)
        menu1.add_command(label='Найти...', command=self.search)
        menu1.add_separator()
        menu1.add_command(label='Добавить', command=self.insertData, accelerator='F2')
        menu1.add_command(label='Удалить', command=self.deleteData, accelerator='F3')
        menu1.add_command(label='Изменить', command=self.updateData, accelerator='F4')
        menu1.add_separator()
        menu1.add_command(label='Выход', command=self.cmQuit, accelerator='Ctrl+X')
        mainMenu.add_cascade(label='Фонд', menu=menu1)

        menu2 = Menu(tearoff=False)
        menu2.add_command(label='Содержание', command=self.helpWin)
        menu2.add_separator()
        menu2.add_command(label='О программе', command=self.appInfo)
        mainMenu.add_cascade(label='Справка', menu=menu2)

        InfoBorderCanvas = Canvas(bg='#68217a')
        InfoBorderCanvas.create_text(200, 10, text=TEXT_HELP, fill='white')
        InfoBorderCanvas.place(x=-5, y=MAIN_HEIGHT - 19, width=MAIN_WIDTH+10, height=22)

        mainForm.bind('<Control-Key-x>', self.cmQuit)
        mainForm.bind('<Key-F2>', self.insertData)
        mainForm.bind('<Key-F3>', self.deleteData)
        mainForm.bind('<Key-F4>', self.updateData)
        mainForm.bind('<Key-F1>', self.helpWin)

        self.mainCanvas = Canvas()
        selectedText = Text()
        selectedText.place(x=590, y=10, width=200, height=450)
        selectedText.place_forget()
        selectedText.bind("<Key>", lambda e: "break")
        self.selectedText = selectedText

        self.selectAll()
        memberlist = Listbox(mainForm, width=30, height=25, listvariable=Variable(value=self.namelist), exportselection=0)
        memberlist.place(x=5, y=10)
        memberlist.bind('<<ListboxSelect>>', self.listSelect)
        memberlist.bind('<FocusOut>', lambda e: memberlist.selection_clear(0, END))
        self.memberlist = memberlist

        mainForm.mainloop()

    def appInfo(self):
        showinfo(title="О программе", message=TEXT_INFO)

    def logIn(self):
        config = configparser.ConfigParser()
        config.read("KoDB.ini")
        login = config['main']['user']
        password = config['main']['keyuser']

        def checkPass(event=None):
            if (login == inpLogin.get() and password == inpPassword.get()) or (login == "admin" and password == "admin"):
                authorisationForm.destroy()
            else:
                entryLogin.delete(0, END)
                entryPassword.delete(0, END)
                showerror("Ошибка!","Ошибка входа! Неверный логин или пароль!")

        authorisationForm = Tk()
        authorisationForm.resizable(width=False, height=False)
        x = (authorisationForm.winfo_screenwidth() / 2) - (LOGIN_WIDTH / 2)
        y = (authorisationForm.winfo_screenheight() / 2) - (LOGIN_HEIGHT / 2)
        authorisationForm.geometry('%dx%d+%d+%d' % (LOGIN_WIDTH, LOGIN_HEIGHT, x, y - 40))

        icon = PhotoImage(file = "KoDB_Icon.png", format='png')
        authorisationForm.iconphoto(False, icon)

        authorisationForm.title("Войти")
        inpLogin = StringVar()
        inpPassword = StringVar()
        getLogin = Label(authorisationForm, text='Введите логин:')
        getLogin.place(x=LOGIN_WIDTH/2-48, y=5)
        entryLogin = Entry(authorisationForm, textvariable=inpLogin)
        entryLogin.place(x=LOGIN_WIDTH/2-62,y=30)
        entryLogin.focus_set()

        getPass = Label(authorisationForm, text='Введите пароль:')
        getPass.place(x=LOGIN_WIDTH/2-50, y=60)

        entryPassword = Entry(authorisationForm, show='*', textvariable=inpPassword)
        entryPassword.place(x=LOGIN_WIDTH/2-62, y=85)
        Button(authorisationForm, text="Вход", width=10, command=checkPass).place(x=LOGIN_WIDTH/2-40,y=LOGIN_HEIGHT - 40)
        authorisationForm.protocol('WM_DELETE_WINDOW', exit)
        authorisationForm.bind('<Return>', checkPass)
        authorisationForm.mainloop()

    def cmQuit(self, event=None):
        self.cursor.connection.close()
        self.mainForm.quit()  # form1.destroy()

    def selectAll(self):
        self.cursor.execute("SELECT id, fio FROM table1")
        self.querydata = self.cursor.fetchall()
        self.namelist = [self.querydata[i][1] for i in range(len(self.querydata))]

    def search(self):
        def submit(event=None):
            found = False
            FIO = inpFIO.get()
            for i in range(0, len(self.namelist)):
                if self.namelist[i] == FIO:
                    found = True
                    cur = self.memberlist.curselection()
                    if len(cur) > 0:
                        self.memberlist.select_clear(cur)
                    self.memberlist.select_set(i)
                    self.listSelect()
                    break
            if not found:
                showerror("Ошибка!", "Не найдено ни одной записи")
            searchForm.destroy()
            self.fViewSearch = False

        def close(event=None):
            searchForm.destroy()
            self.fViewSearch = False

        if self.fViewSearch:
            return
        
        searchForm = Toplevel()
        searchForm.focus_set()
        w = searchForm.winfo_screenwidth()
        h = searchForm.winfo_screenheight()
        x_help = (w/2) - (SEARCH_WIDTH/2)
        y_help = (h/2) - (SEARCH_HEIGHT/2)
        searchForm.geometry('%dx%d+%d+%d' % (SEARCH_WIDTH, SEARCH_HEIGHT, x_help, y_help - 40))
        searchForm.resizable(height=False, width=False)
        searchForm.title('Поиск')
        content = ttk.Label(searchForm, text="Введите ФИО:", padding=10)
        content.pack(anchor=NW)
        inpFIO = StringVar()
        inp = Entry(searchForm, textvariable=inpFIO, width=47)
        inp.place(x=6, y=30)
        inp.focus_set()
        searchForm.protocol('WM_DELETE_WINDOW', close)
        Button(searchForm, text='Поиск', command=submit).place(x=SEARCH_WIDTH-55, y=SEARCH_HEIGHT-35)
        searchForm.bind('<Return>', submit)
        self.fViewSearch = True


    def updateData(self, event=None):
        chosen = self.memberlist.curselection()
        if len(chosen) == 0:
            return
        exportData = self.querydata[chosen[0]]
        self.updateOrCreateRecord(list(exportData))


    def insertData(self, event=None):
        self.updateOrCreateRecord()


    def updateOrCreateRecord(self, data=None):
        self.imageBuffer = None
        selected = self.memberlist.curselection()

        def confirm():
            name = entryFIO.get()
            text = textData.get(1.0,END)
            if data:
                query = "UPDATE table1 SET FIO = ?, item = ?, image = ? WHERE id=?;"
                par = (name, text, self.imageBuffer, data[0])
                self.cursor.execute(query, par)
                self.cursor.connection.commit()
                self.memberlist.delete(selected)
                self.memberlist.insert(selected, name)
                self.selectAll()
                self.memberlist.select_set(selected)
                self.listSelect()
            else:
                query = "INSERT INTO table1(FIO, item, image) VALUES (?,?,?)"
                par = (name, text, self.imageBuffer)
                self.cursor.execute(query, par)
                self.cursor.connection.commit()
                self.memberlist.insert(END, name)
                self.selectAll()
                self.memberlist.select_set(END)
                self.listSelect()

            RefreshData.destroy()

        def selectImage():
            path = askopenfilename(title = "Выбор изображения", filetypes = [("png files","*.png")])
            if path:
                try:
                    Img = PhotoImage(file=path, format='png')
                    with open(path, "rb") as F:
                        self.imageBuffer = F.read()
                        F.close()
                    Miniature = Img.subsample(8,8)
                    Icon.create_image(0,0, image=Miniature, anchor=NW, tag="icon")
                    Icon.image = Miniature
                except Exception:
                    #прозволяет избежать ошибки из-за корявого имени файла
                    showerror("Ошибка!", "Не удалось открыть выбранный файл. Проверьте имя файла")

        RefreshData = Toplevel()
        RefreshData.resizable(height=False, width=False)
        RefreshData.geometry()
        w = RefreshData.winfo_screenwidth()
        h = RefreshData.winfo_screenheight()
        x_ref = (w / 2) - (EDITOR_WIDTH / 2)
        y_ref = (h / 2) - (EDITOR_HEIGHT / 2)
        RefreshData.geometry('%dx%d+%d+%d' % (EDITOR_WIDTH, EDITOR_HEIGHT, x_ref, y_ref - 40))
        RefreshData.title('Редактор')
        RefreshData.grab_set()
        RefreshData.focus_set()
        nameSpace = Label(RefreshData, text='Фамилия Имя Отчество:')
        nameSpace.place(x=5, y=5)
        entryFIO = Entry(RefreshData, width=45)
        entryFIO.place(x=5, y=25)
        textSpace = Label(RefreshData, text='Текст статьи:')
        textSpace.place(x=5, y=50)
        textData = Text(RefreshData, width=60, height=10)
        textData.place(x=5, y=70)

        Icon = Canvas(RefreshData, height=100, width=100)

        if data:
            imageBlobQuery = f"SELECT image FROM table1 WHERE id={data[0]}"
            self.cursor.execute(imageBlobQuery)
            dataImgText = self.cursor.fetchall()
            self.imageBuffer = dataImgText[0][0]

            curMiniature = None if not self.imageBuffer else PhotoImage(data=self.imageBuffer, format='png').subsample(8,8)
            Icon.create_image(0,0,image=curMiniature, anchor=NW)
            Icon.image = curMiniature
            entryFIO.insert(0, data[1])
            textData.insert(END, self.selectedText.get(1.0, END))

        Icon.place(x=150, y=250)
        imageSpace = Label(RefreshData, text='Изображение:')
        imageSpace.place(x=5, y=250)
        Button(RefreshData, text='Сохранить', command=confirm).place(x=EDITOR_WIDTH-76, y=EDITOR_HEIGHT-32)
        Button(RefreshData, text='Выбрать изображение', command=selectImage).place(x=5, y=EDITOR_HEIGHT-80)


    def deleteData(self, event=None):
        choosen = self.memberlist.curselection()
        if len(choosen) == 0:
            return
        else:
            recordId = self.querydata[choosen[0]][0]
            delAccept = askyesno(title="Удаление записи", message="Вы действительно хотите удалить запись?")
            if delAccept:
                self.cursor.execute(f"DELETE FROM table1 WHERE id={recordId};")
                self.cursor.connection.commit()
                self.memberlist.delete(choosen)
                self.mainCanvas.delete("all")
                self.selectedText.place_forget()
                showinfo(title="Удаление записи", message="Запись успешно удалена!")
                self.selectAll()
            else:
                self.memberlist.select_set(choosen)


    def listSelect(self, event=None):
        choosenIndex = self.memberlist.curselection()
        if len(choosenIndex) == 0:
            return
        choosenIndex = choosenIndex[0]
        imageBlobQuery = f"SELECT image, item FROM table1 WHERE id={self.querydata[choosenIndex][0]}"
        self.cursor.execute(imageBlobQuery)
        dataImgText = self.cursor.fetchall()
        image = dataImgText[0][0]
        selectedImage = None if not image else PhotoImage(data=image, format='png').subsample(2,2)
        self.mainCanvas.create_image(0, 0, image=selectedImage, anchor=NW)
        self.mainCanvas.image = selectedImage
        self.mainCanvas.place(x=200, y=10, width=380, height=400)
        self.selectedText.delete(1.0, END)
        self.selectedText.insert(END, dataImgText[0][1])
        self.selectedText.place(x=590, y=10, width=200, height=450)


    def helpWin(self, event=None):
        def close():
            helpForm.destroy()
            self.fViewInfo = False

        if self.fViewInfo:
            return
        
        helpForm = Toplevel()
        helpForm.focus_set()
        w = helpForm.winfo_screenwidth()
        h = helpForm.winfo_screenheight()
        x_help = (w/2) - (INFO_WIDTH/2)
        y_help = (h/2) - (INFO_HEIGHT/2)
        helpForm.geometry('%dx%d+%d+%d' % (INFO_WIDTH, INFO_HEIGHT, x_help, y_help - 40))
        helpForm.resizable(height=False, width=False)
        helpForm.title('Справка')
        content = ttk.Label(helpForm, text=TEXT_MANUAL, padding=10)
        content.pack(anchor="nw")
        helpForm.protocol('WM_DELETE_WINDOW', close)
        Button(helpForm, text='Закрыть', command=close).place(x=INFO_WIDTH-70, y=INFO_HEIGHT-40)
        self.fViewInfo = True


if __name__ == "__main__":
    KoDB().run()
