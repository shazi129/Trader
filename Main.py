#用pyside6的库来实现一个简单的窗口程序
#导入PySide6模块
from PySide6.QtWidgets import QApplication, QLabel

#如何安装pyside6库
#pip install PySide6
#创建一个应用程序对象
app = QApplication([])
#设置窗口标题
app.setApplicationName("Trader")
#设置窗口大小
app.setApplicationDisplayName("Trader")


#创建一个标签对象
label = QLabel("Hello World!")  
#显示标签
label.show()
#启动应用程序的主事件循环
app.exec()

#运行程序，可以看到一个窗口弹出来，上面显示Hello World!字样

#运行结果如下：
#Hello World!

#写一条sql语句，结合tableA和tableB，输出它们某一列数值的比
#select a.column1/b.column2 from tableA a join tableB b on a.id=b.id

#如何使用PySide6的UI设计工具
#PySide6提供了一个名为Qt Design的UI设计工具，可以用来设计窗口程序的界面
#Qt Design的下载地址：https://www.qt.io/download-qt-installer
#下载安装后，可以打开Qt Design，然后设计窗口程序的界面，保存为.ui文件
#然后使用PySide6提供的uic模块将.ui文件转换为.py文件，然后在程序中导入这个.py文件即可


if __name__ == "__main__":
    print("Hello World!")

