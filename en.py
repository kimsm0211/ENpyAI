import string

ALPHABET = string.ascii_uppercase

# 실제 회전자 배선과 턴오버 직전 창에 보이는 문자.
# 예: I번 회전자는 창이 Q일 때 다음 키 입력에서
# 자신과 왼쪽 회전자가 함께 전진합니다.
ROTOR_SPECS = {
    "I":    ("EKMFLGDQVZNTOWYHXUSPAIBRCJ", "Q"),
    "II":   ("AJDKSIRUXBLHWTMCQGZNPYFVOE", "E"),
    "III":  ("BDFHJLCPRTXVZNYEIWGAKMUSQO", "V"),
    "IV":   ("ESOVPZJAYQUIRHXLNFTGKDCMWB", "J"),
    "V":    ("VZBRGITYUPSDNHLXAWMJQOFECK", "Z"),
    "VI":   ("JPGVOUMFYQBENHZRDKASXLICTW", "ZM"),
    "VII":  ("NZJHGRCXMYSWBOUFAIVLPEKQDT", "ZM"),
    "VIII": ("FKQHTLXOCBJSPDZRAMEWNIUYGV", "ZM"),
}

REFLECTOR_SPECS = {
    "B": "YRUHQSLDPXNGOKMIEBFZCWVJAT",
    "C": "FVPJIAOYEDRZXWGCTKUQSBNMHL",
}


def to_number(letter):
    return ord(letter) - ord("A")


def normalize_text(text):
    """영문 소문자는 대문자로 바꾸고 공백은 제거합니다."""
    result = []

    for char in text:
        if char in string.ascii_letters:
            result.append(char.upper())
        elif char.isspace():
            continue
        else:
            raise ValueError(
                f"지원하지 않는 문자: {char!r}. "
                "A~Z, a~z, 공백만 입력하세요."
            )

    return "".join(result)


def parse_three_settings(value):
    """
    다음 형식을 모두 지원합니다.
    ABC
    A B C
    01 02 03

    반환값은 0~25 정수 3개입니다.
    """
    tokens = value.upper().split()

    if len(tokens) == 1 and len(tokens[0]) == 3:
        tokens = list(tokens[0])

    if len(tokens) != 3:
        raise ValueError(
            "ABC, A B C 또는 01 02 03 형식으로 입력하세요."
        )

    settings = []

    for token in tokens:
        if len(token) == 1 and token in ALPHABET:
            settings.append(to_number(token))
        elif token.isascii() and token.isdecimal():
            number = int(token)
            if not 1 <= number <= 26:
                raise ValueError("숫자 설정은 01~26이어야 합니다.")
            settings.append(number - 1)
        else:
            raise ValueError(f"잘못된 설정값: {token!r}")

    return settings


def make_plugboard(value):
    """
    입력 예: AV BS CG DL FU HZ IN KM OW RX

    연결하지 않은 문자는 자기 자신으로 연결됩니다.
    """
    pairs = value.upper().split()

    if len(pairs) > 13:
        raise ValueError("플러그보드는 최대 13쌍입니다.")

    mapping = list(range(26))
    used = set()

    for pair in pairs:
        if len(pair) != 2 or any(c not in ALPHABET for c in pair):
            raise ValueError(
                f"잘못된 플러그 쌍: {pair!r}. AB처럼 입력하세요."
            )

        a, b = pair

        if a == b:
            raise ValueError("같은 문자를 서로 연결할 수 없습니다.")

        if a in used or b in used:
            raise ValueError(
                f"문자를 중복해서 연결할 수 없습니다: {pair}"
            )

        used.update((a, b))
        x, y = to_number(a), to_number(b)
        mapping[x], mapping[y] = y, x

    return mapping


class Rotor:
    def __init__(self, name, ring, position):
        wiring, turnover_letters = ROTOR_SPECS[name]

        self.name = name
        self.ring = ring
        self.position = position
        self.turnover_positions = {
            to_number(c) for c in turnover_letters
        }

        self.forward_wiring = [to_number(c) for c in wiring]

        self.backward_wiring = [0] * 26
        for input_contact, output_contact in enumerate(
            self.forward_wiring
        ):
            self.backward_wiring[output_contact] = input_contact

    def at_turnover(self):
        # position은 창에 보이는 문자 기준입니다.
        # 따라서 이 검사에는 링 설정을 빼지 않습니다.
        return self.position in self.turnover_positions

    def step(self):
        self.position = (self.position + 1) % 26

    def forward(self, value):
        """오른쪽에서 왼쪽으로 진행하는 신호."""
        offset = self.position - self.ring
        contact = (value + offset) % 26
        wired = self.forward_wiring[contact]
        return (wired - offset) % 26

    def backward(self, value):
        """왼쪽에서 오른쪽으로 돌아오는 신호."""
        offset = self.position - self.ring
        contact = (value + offset) % 26
        wired = self.backward_wiring[contact]
        return (wired - offset) % 26


class EnigmaM3:
    def __init__(
        self,
        rotor_order="I II III",
        reflector="B",
        rings="01 01 01",
        positions="AAA",
        plugboard="",
    ):
        names = rotor_order.upper().split()

        if len(names) != 3:
            raise ValueError("회전자는 정확히 3개를 입력하세요.")

        if len(set(names)) != 3:
            raise ValueError("같은 회전자를 중복 사용할 수 없습니다.")

        for name in names:
            if name not in ROTOR_SPECS:
                raise ValueError(f"지원하지 않는 회전자: {name}")

        reflector = reflector.strip().upper()
        if reflector not in REFLECTOR_SPECS:
            raise ValueError("반사판은 B 또는 C를 선택하세요.")

        ring_values = parse_three_settings(rings)
        position_values = parse_three_settings(positions)

        # 모든 설정은 기계를 정면에서 본 왼쪽 → 오른쪽 순서.
        self.rotors = [
            Rotor(name, ring, position)
            for name, ring, position in zip(
                names, ring_values, position_values
            )
        ]

        self.reflector = [
            to_number(c) for c in REFLECTOR_SPECS[reflector]
        ]
        self.plugboard = make_plugboard(plugboard)
        self.initial_positions = tuple(position_values)

    def get_positions(self):
        return "".join(
            ALPHABET[rotor.position] for rotor in self.rotors
        )

    def reset(self):
        """처음 지정한 시작 위치로 되돌립니다."""
        for rotor, position in zip(
            self.rotors, self.initial_positions
        ):
            rotor.position = position

    def set_positions(self, positions):
        """현재 창 위치만 바꿉니다. reset 기준은 바꾸지 않습니다."""
        values = parse_three_settings(positions)
        for rotor, value in zip(self.rotors, values):
            rotor.position = value

    def _step_rotors(self):
        left, middle, right = self.rotors

        # 반드시 움직이기 전 상태를 먼저 확인합니다.
        middle_at_turnover = middle.at_turnover()
        right_at_turnover = right.at_turnover()

        if middle_at_turnover:
            left.step()

        # 가운데 회전자의 더블 스테핑을 재현합니다.
        if middle_at_turnover or right_at_turnover:
            middle.step()

        right.step()

    def _press(self, letter):
        # 실제 동작처럼 먼저 회전한 뒤 신호를 통과시킵니다.
        self._step_rotors()

        value = self.plugboard[to_number(letter)]

        # 오른쪽 → 가운데 → 왼쪽
        for rotor in reversed(self.rotors):
            value = rotor.forward(value)

        value = self.reflector[value]

        # 왼쪽 → 가운데 → 오른쪽
        for rotor in self.rotors:
            value = rotor.backward(value)

        value = self.plugboard[value]
        return ALPHABET[value]

    def process(self, text, trace=False):
        """
        암호화와 복호화에 같은 함수를 사용합니다.
        호출이 끝나도 회전자 위치는 유지됩니다.

        trace=True이면 글자마다 회전자 위치를 출력합니다.
        """
        # 전체 입력을 먼저 검사해 오류 시 회전하지 않게 합니다.
        text = normalize_text(text)
        result = []

        for letter in text:
            before = self.get_positions()
            output = self._press(letter)
            result.append(output)

            if trace:
                after = self.get_positions()
                print(f"{before} -> {after} | {letter} -> {output}")

        return "".join(result)


def group_five(text):
    return " ".join(
        text[i:i + 5] for i in range(0, len(text), 5)
    )


def self_test():
    # 기본 설정의 알려진 출력 확인
    machine = EnigmaM3()
    assert machine.process("AAAAA") == "BDZGO"

    machine.reset()
    assert machine.process("HELLOWORLD") == "ILBDAAMTAZ"

    # 더블 스테핑: 가운데 회전자가 연속 두 번 움직임
    machine = EnigmaM3(positions="ADU")
    observed = [machine.get_positions()]

    for _ in range(3):
        machine.process("A")
        observed.append(machine.get_positions())

    assert observed == ["ADU", "ADV", "AEW", "BFX"]

    # 창의 문자 기준 턴오버는 링 설정을 바꿔도 동일
    machine = EnigmaM3(rings="07 12 23", positions="ADU")
    observed = [machine.get_positions()]

    for _ in range(3):
        machine.process("A")
        observed.append(machine.get_positions())

    assert observed == ["ADU", "ADV", "AEW", "BFX"]

    # VI~VIII의 두 턴오버 위치 확인
    for name in ("VI", "VII", "VIII"):
        for start, expected in (("AAM", "ABN"), ("AAZ", "ABA")):
            machine = EnigmaM3(
                rotor_order=f"I II {name}",
                positions=start,
            )
            machine.process("A")
            assert machine.get_positions() == expected

    # 다른 반사판, 링, 회전자, 플러그보드로 왕복 확인
    machine = EnigmaM3(
        rotor_order="VIII VI II",
        reflector="C",
        rings="03 17 26",
        positions="KCH",
        plugboard="AV BS CG DL FU HZ IN KM OW RX",
    )

    plain = "ENIGMAMTHREE" * 100
    cipher = machine.process(plain)

    machine.reset()
    assert machine.process(cipher) == plain

    print("자체 테스트 통과")


def ask(prompt, default):
    value = input(f"{prompt} [{default}]: ").strip()
    return value if value else default


def main():
    print("=== Enigma M3 ===")
    print("설정 순서는 모두 왼쪽 → 가운데 → 오른쪽입니다.")
    print("엔터를 누르면 대괄호 안의 기본값을 사용합니다.\n")

    try:
        machine = EnigmaM3(
            rotor_order=ask("회전자 순서", "I II III"),
            reflector=ask("반사판 B/C", "B"),
            rings=ask("링 설정: ABC 또는 01 02 03", "01 01 01"),
            positions=ask("시작 위치: ABC 또는 01 02 03", "AAA"),
            plugboard=input(
                "플러그보드: AV BS CG ... / 없으면 엔터: "
            ).strip(),
        )

        trace = input("글자별 회전 과정 표시? (y/N): ").lower() == "y"

        print("\n암호화와 복호화는 같은 방식으로 처리합니다.")
        print("공백은 제거되며 숫자·기호·한글은 입력할 수 없습니다.")

        while True:
            print(f"\n현재 위치: {machine.get_positions()}")
            print("1: 입력 처리  2: 시작 위치로 복원  0: 종료")
            command = input("> ").strip()

            if command == "0":
                break

            if command == "2":
                machine.reset()
                print("처음 설정한 시작 위치로 되돌렸습니다.")
                continue

            if command != "1":
                print("0, 1, 2 중에서 선택하세요.")
                continue

            try:
                text = input("평문 또는 암호문: ")
                result = machine.process(text, trace=trace)
                print("결과:", group_five(result))
            except ValueError as error:
                print("입력 오류:", error)

    except ValueError as error:
        print("설정 오류:", error)


if __name__ == "__main__":
    import sys

    if "--test" in sys.argv:
        self_test()
    else:
        main()
