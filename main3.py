from tkinter import *
import tkinter.messagebox


def fun1():
    print('fun1')
    fun2()


def fun2():
    print('fun2')


class Application(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.pack()
        self.create_widgets()

    def create_widgets(self):
        self.text_input = Entry(self)
        self.text_input.pack()
        self.alert_button = Button(self, text='popup',
                                   command=self.popup)
        self.alert_button.pack()

    def popup(self):
        str = self.text_input.get() or 'nothing!'
        tkinter.messagebox.showinfo('Text!', str)


if __name__ == '__main__':
    app = Application()
    app.master.title('myTitle')
    app.mainloop()
