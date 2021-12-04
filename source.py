from typing import Union, Optional, Generator


class Word:
    def __init__(self, arg: Union[list[int], int, None] = None):
        if arg is None:
            self.__array = []
            return
        t = type(arg)
        if t == list:
            for i, elem in enumerate(arg):
                if type(elem) != int or elem not in [0, 1]:
                    raise ValueError(f'Неверный {i}-й элемент слова: {elem}. Должен быть нулем или единицей')
            self.__array = arg
        elif t == int:
            self.__array = [0 for _ in range(arg)]
        else:
            raise ValueError(f'Неверный тип параметра конструктора слова: {t}')

    def __str__(self) -> str:
        string = ''
        for i, elem in enumerate(self.__array):
            string += str(elem)
            if i % 4 == 3 and i != len(self.__array) - 1:
                string += '.'
        return string

    def __len__(self) -> int:
        return len(self.__array)

    def __add__(self, other):
        if type(other) != Word:
            raise ValueError('Слово можно сложить только со словом')
        if len(self) != len(other):
            raise ValueError('Можно складывать только слова одинаковой длины')
        return Word(list(map(lambda x: (x[0] + x[1]) % 2, zip(self.__array, other.__array))))

    def __getitem__(self, item):
        t = type(item)
        if t == int:
            return self.__array[item]
        elif t == slice:
            return Word(self.__array[item])
        else:
            raise ValueError('Неверный тип параметра оператора извлечения среза или элемента слова')

    def __setitem__(self, key, value):
        if type(key) != int:
            raise ValueError('Индекс должен быть целочисленным')
        if type(value) != int or value not in [0, 1]:
            raise ValueError('Значение элемента слова должно быть нулем или единицей')
        self.__array[key] = value

    def __iter__(self):
        return iter(self.__array)

    def concatenate(self, other):
        return Word(self.__array + other.__array)

    def weight(self) -> int:
        return sum(self.__array)

    def __rshift__(self, num: int):
        return Word(self.__array[-num:] + self.__array[:-num])


def generate_words(length: int) -> Generator[Word, None, None]:
    if length == 1:
        yield Word([0])
        yield Word([1])
    else:
        for word in generate_words(length - 1):
            yield word.concatenate(Word([1]))
            yield word.concatenate(Word([0]))


class Polynomial:
    def __init__(self, arg: Union[Word, int, None] = None) -> None:
        if arg is None:
            self.__coefficients = Word()
            return
        t = type(arg)
        if t == Word:
            last = len(arg) - 1
            while last > 0 and arg[last] == 0:
                last -= 1
            self.__coefficients = arg[:last + 1]
        elif t == int:
            if arg >= 0:
                self.__coefficients = Word(arg).concatenate(Word([1]))
            else:
                raise ValueError('Степень многочлена не может быть отрицательной')
        else:
            raise ValueError(f'Неверный тип параметра конструктора: {t}')

    def pow(self) -> int:
        return len(self.__coefficients) - 1

    def weight(self) -> int:
        return self.__coefficients.weight()

    def __str__(self) -> str:
        summands = []
        for i, coefficient in enumerate(self.__coefficients):
            if coefficient == 1:
                if i == 0:
                    summands.append('1')
                elif i == 1:
                    summands.append('x')
                else:
                    summands.append(f'x^{i}')
        if summands:
            return ' + '.join(summands)
        else:
            return '0'

    def __add__(self, other):
        if type(other) != Polynomial:
            raise ValueError('Полином можно сложить только с полиномом')
        sum_1, sum_2 = self, other
        if sum_1.pow() < sum_2.pow():
            sum_1, sum_2 = sum_2, sum_1
        return Polynomial(sum_1.__coefficients + sum_2.to_word(sum_1.pow() + 1))

    def __mul__(self, other):
        if type(other) != Polynomial:
            raise ValueError('Полином можно умножить только на полиномом')
        result = Polynomial()
        for i, coefficient in enumerate(other.__coefficients):
            if coefficient == 1:
                result += Polynomial(Word(i).concatenate(self.__coefficients))
        return result

    def __divmod__(self, other):
        if type(other) != Polynomial:
            raise ValueError(f'Невозможно разделить полином на {type(other)}')
        divisible = self
        divider = other
        division = Polynomial()
        while divisible.pow() >= divider.pow():
            polynomial = Polynomial(divisible.pow() - divider.pow())
            division += polynomial
            divisible += polynomial * divider
        return division, divisible

    def __floordiv__(self, other):
        if type(other) != Polynomial:
            raise ValueError(f'Невозможно разделить полином на {type(other)}')
        return divmod(self, other)[0]

    def __mod__(self, other):
        if type(other) != Polynomial:
            raise ValueError(f'Невозможно посчитать остаток от деления полинома на {type(other)}')
        return divmod(self, other)[1]

    def to_word(self, length: int) -> Word:
        if length < self.pow() + 1:
            raise ValueError('Слишком короткое слово')
        return self.__coefficients.concatenate(Word(length - self.pow() - 1))


class CyclicCode:
    def __init__(self, length: int, polynomial: Polynomial, package_size: int) -> None:
        self.__length = length
        self.__polynomial = polynomial
        self.__word_length = length - polynomial.pow()
        self.__errors = (self.__word_length - 1) // 2
        self.__package = set()
        for word in generate_words(package_size):
            word = word.concatenate(Word(self.__word_length - package_size))
            for i in range(length):
                self.__package.add(tuple(word >> i))

    def __str__(self) -> str:
        return f'Циклический код ({len(self)}, {len(self) - self.__polynomial.pow()}) ' \
               f'с порождающим многочленом {self.__polynomial}'

    def __len__(self) -> int:
        return self.__length

    def encode(self, word: Word) -> Word:
        if len(word) != self.__word_length:
            raise ValueError('Неверная длина кодируемого слова')
        return (Polynomial(word) * self.__polynomial).to_word(len(self))

    def decode(self, word: Word) -> Word:
        if len(word) != len(self):
            raise ValueError('Неверная длина декодируемого слова')
        return (Polynomial(word) // self.__polynomial).to_word(self.__word_length)

    def find_error(self, word: Word) -> Optional[Word]:
        if len(word) != len(self):
            raise ValueError('Неверная длина слова для поиска ошибки')
        remainder = Polynomial(word) % self.__polynomial
        for i in range(0, len(self)):
            syndrome = (Polynomial(i) * remainder) % self.__polynomial
            if syndrome.weight() <= self.__errors:
                return syndrome.to_word(len(self)) >> (len(self) - i)

    def find_error_in_package(self, word: Word) -> Optional[Word]:
        if len(word) != len(self):
            raise ValueError('Неверная длина слова для поиска ошибки')
        remainder = Polynomial(word) % self.__polynomial
        for i in range(0, len(self)):
            syndrome = (Polynomial(i) * remainder) % self.__polynomial
            if tuple(syndrome.to_word(self.__word_length)) in self.__package:
                return syndrome.to_word(len(self)) >> (len(self) - i)


def error_correction(code: CyclicCode, word: Word, error: Word) -> None:
    print(f'Исходное слово: {word}')
    message = code.encode(word)
    print(f'Закодированное сообщение: {message}')
    print(f'Ошибка: {error}')
    error_message = message + error
    print(f'Сообщение с ошибкой: {error_message}')
    found_error = code.find_error(error_message)
    print(f'Поиск ошибки: {found_error}')
    corrected_message = error_message + found_error
    print(f'Исправление ошибки: {corrected_message}')
    decoded_word = code.decode(corrected_message)
    print(f'Декодированное слово: {decoded_word}')


def error_packages_correction(code: CyclicCode, word: Word, error_package: list[Word]) -> None:
    print(f'Исходное слово: {word}')
    message = code.encode(word)
    print(f'Закодированное сообщение: {message}')
    print('Рассмотрим ошибки в пакете: ')
    for error in error_package:
        print()
        print(f'Ошибка: {error}')
        error_message = message + error
        print(f'Сообщение с ошибкой: {error_message}')
        found_error = code.find_error_in_package(error_message)
        if found_error is not None:
            print(f'Поиск ошибки: {found_error}')
            corrected_message = error_message + found_error
            print(f'Исправление ошибки: {corrected_message}')
            decoded_word = code.decode(corrected_message)
            print(f'Декодированное слово: {decoded_word}')
            print()
        else:
            print('Исправление ошибки невозможно')


def main():
    code = CyclicCode(7, Polynomial(Word([1, 0, 1, 1])), 1)
    print(f'Используем код: {code}')
    print()
    error_correction(code, Word([1, 0, 0, 1]), Word([0, 1, 0, 0, 0, 0, 0]))
    print()
    error_correction(code, Word([1, 0, 0, 1]), Word([0, 1, 1, 0, 0, 0, 0]))
    print()
    error_correction(code, Word([1, 0, 0, 1]), Word([0, 1, 1, 1, 0, 0, 0]))

    print()
    code = CyclicCode(15, Polynomial(Word([1, 0, 0, 1, 1, 1, 1, 0, 0])), 4)
    print(f'Используем код: {code}')
    print()
    error_packages_correction(code, Word([1, 0, 0, 1, 0, 0, 0, 1, 1]),
                              [Word([1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])])
    print()
    error_packages_correction(code, Word([1, 0, 0, 1, 0, 0, 0, 1, 1]),
                              [Word([1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
                               Word([1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])])
    print()
    error_packages_correction(code, Word([1, 0, 0, 1, 0, 0, 0, 1, 1]),
                              [Word([1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
                               Word([1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
                               Word([1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])])
    print()
    error_packages_correction(code, Word([1, 0, 0, 1, 0, 0, 0, 1, 1]),
                              [Word([1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
                               Word([1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
                               Word([1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])])


if __name__ == '__main__':
    main()
