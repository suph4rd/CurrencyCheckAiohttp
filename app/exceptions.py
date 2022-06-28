

class HandleError(Exception):

    def __str__(self):
        print(super().__str__())
        return "Ошибка распаковки ответа!"
