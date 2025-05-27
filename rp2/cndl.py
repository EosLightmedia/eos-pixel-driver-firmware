import sys

if sys.platform == 'rp2':
    from ulab import numpy as np
else:
    import numpy as np

class CNDL:
    def __init__(self, data):
        print('Loading CNDL')

        self.graph = {}
        for id1, data1 in data['operation'].items():
            self.graph[id1] = []
            for input_val in data1['input']:
                if isinstance(input_val, str) and input_val in data['operation']:
                    if input_val not in self.graph:
                        self.graph[input_val] = []
                    self.graph[input_val].append(id1)

        personality_nodes = []
        for entry in data.get('personality', []):
            if len(entry) >= 2 and isinstance(entry[1], str) and entry[1] in data['operation']:
                personality_nodes.append(entry[1])

        if not personality_nodes:
            personality_nodes = list(data['operation'].keys())

        visited = set()
        result = []

        def visit_node(node):
            if node in visited:
                return
            visited.add(node)

            if node in data['operation']:
                for input_val in data['operation'][node]['input']:
                    if isinstance(input_val, str) and input_val in data['operation']:
                        visit_node(input_val)

            result.append(node)

        for node in personality_nodes:
            visit_node(node)

        for node in data['operation']:
            if node not in visited:
                visit_node(node)

        code_lines = []
        ids = []

        for node_id in result:
            if node_id in data['operation']:
                op_data = data['operation'][node_id]
                code_line = f"{node_id} = {op_data['code']}({','.join(str(i) for i in op_data['input'])})"
                code_lines.append(code_line)
                ids.append(node_id)

        for i, entry in enumerate(data.get('personality', [])):
            value = entry[1]
            if isinstance(value, str) and value in data['operation']:
                code_line = f"OUT({i}, {value})"
                code_lines.append(code_line)
            else:
                code_line = f"OUT({i}, {value})"
                code_lines.append(code_line)

        self.code = '\n'.join(code_lines); print(f'{self.code=}')
        self.map = np.array(data['map'])

        self.size = (len(self.map),len(data['personality']))
        self.output: np.ndarray = np.zeros((self.size[0], self.size[1]))
        print(f'Output buffer: {self.output.shape}')
        self.inputs: dict[str, float] = {_input: 0.0 for _input in data['influence']}
        self.locals: dict[str, np.ndarray] = {_id: np.zeros(self.size[0]) for _id in ids}

        self.operations: dict[str, object] = {
                'OUT': lambda x=0, y=0: self._out(x, y),
                'X': lambda: self.map[:, 0],
                'Y': lambda: self.map[:, 1],
                'Z': lambda: self.map[:, 2],
                'PI': lambda: np.pi,
                'ADD': lambda x=0, y=0: x + y,
                'MUL': lambda x=1, y=1: x * y,
                'WAVE': lambda x=0: (np.sin(((x - 0.25) * np.pi * 2)) + 1) / 2,
                'FRAC': lambda x=0, y=0: x - np.floor(x),
                'FLIP': lambda x=0: 1.0 - abs(x),
                'SIGN': lambda x=0: np.sign(x),
                'ROUND': lambda x=0: np.around(np.array([x]), decimals=0),
                'REVERSE': lambda x=0: -x,
                'SPOT': lambda x=0: -(x * x),
                'ABS': lambda x=0: np.abs(x),
                'SYM2UNI': lambda x=0: (x + 1) / 2,
                'UNI2SYM': lambda x=0: (x * 2) - 1,
                'CLIP': lambda x=0: np.clip(x, 0, 1),
        }

        print(f'Compiling scene')
        self.bytecode = compile(self.code, '<string>', 'exec')

    def _out(self, index, value):
        self.output[:, index] = value

    def update(self, inputs: dict[str, float]):
        self.inputs.update(inputs)
        _globals = {}
        _globals.update(self.operations)
        _globals.update(self.inputs)
        _globals.update(self.locals)
        _locals = {}
        exec(self.bytecode, _globals, _locals)

        for local in _locals:
            self.locals[local][:] = np.clip(_locals[local], -1, 1)

        self.output[:] = np.clip(self.output[:], 0, 1)

        return _locals
