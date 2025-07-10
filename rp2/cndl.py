import sys

if sys.platform == 'rp2':
    from ulab import numpy as np
else:
    import numpy as np


def order_operations(data) -> list[str]:
    node_graph = {}
    prime_nodes = []
    visited = set()
    result = []
    for node_id, node_data in data['operation'].items():
        node_graph[node_id] = []
        if node_id == 'OUT':
            visited.add(node_id)
            for personality_key in data['personality']:
                for k, v in node_data.items():
                    if k == personality_key:
                        if isinstance(v, str) and v in data['operation']:
                            prime_nodes.append(v)
        else:
            for input_val in node_data['input']:
                if isinstance(input_val, str) and input_val in data['operation']:
                    if input_val not in node_graph:
                        node_graph[input_val] = []
                    node_graph[input_val].append(node_id)

    def visit_node(_node):
        if _node in visited:
            return
        visited.add(_node)
        if _node in data['operation']:
            for _input_val in data['operation'][_node]['input']:
                if isinstance(_input_val, str) and _input_val in data['operation']:
                    visit_node(_input_val)
        result.append(_node)

    for node in prime_nodes:
        visit_node(node)
    for node in data['operation']:
        if node not in visited:
            visit_node(node)
    return result


def compile_to_py(data, result) -> list[str]:
    code_lines = []
    for node_id in result:
        if node_id in data['operation']:
            op_data = data['operation'][node_id]
            code_line = f"{node_id} = {op_data['code']}({','.join(str(i) for i in op_data['input'])})"
            code_lines.append(code_line)
    for i, personality_key in enumerate(data.get('personality', [])):
        value = data['operation']['OUT'][personality_key]
        if isinstance(value, str) and value in data['operation']:
            code_line = f"OUT({i}, {value})"
            code_lines.append(code_line)
        else:
            code_line = f"OUT({i}, {value})"
            code_lines.append(code_line)
    return code_lines


class CNDL:
    def __init__(self, data: dict[str:object]):
        self.code = '\n'.join(compile_to_py(data, order_operations(data)))
        self.bytecode = compile(self.code, '<string>', 'exec')

        self.delta_time = 0.0
        self.map = np.array(data['map'])
        self.personality = data['personality']
        self.size = (len(self.map),len(data['personality']))
        self.output: np.ndarray = np.zeros((self.size[0], self.size[1]))
        self.inputs: dict[str, float] = {_input: 0.0 for _input in data['influence']}
        self.locals: dict[str, np.ndarray] = {_id: np.zeros(self.size[0]) for _id in (order_operations(data))}
        self.operations: dict[str, object] = {
                'OUT': lambda x=0, y=0: self._out(x, y),
                'X': lambda: self.map[:, 0],
                'Y': lambda: self.map[:, 1],
                'Z': lambda: self.map[:, 2],
                'PI': lambda: np.pi,
                'TIME': lambda: self.delta_time,
                'ADD': lambda x=0, y=0: x + y,
                'MUL': lambda x=1, y=1: x * y,
                'WAVE': lambda x=0: (np.sin(((x - 0.25) * np.pi * 2)) + 1) / 2,
                'FRAC': lambda x=0, y=0: x - np.floor(x),
                'FLIP': lambda x=0: 1.0 - abs(x),
                'SIGN': lambda x=0: np.sign(x),
                'ROUND': lambda x=0: np.around(np.array([x]), decimals=0).flatten(),
                'REVERSE': lambda x=0: -x,
                'SPOT': lambda x=0: (-(x * x)) + 1.,
                'ABS': lambda x=0: np.abs(x),
                'SYM2UNI': lambda x=0: (x + 1) / 2,
                'UNI2SYM': lambda x=0: (x * 2) - 1,
                'CLIP': lambda x=0: np.clip(x, 0, 1),
        }

    def _out(self, index, value):
        self.output[:, index] = value

    def update(self, inputs: dict[str, float], delta_time: float = 0.0):
        self.delta_time = delta_time
        self.inputs.update(inputs)
        _globals = {}
        _globals.update(self.operations)
        _globals.update(self.inputs)
        _globals.update(self.locals)
        _locals = {}
        exec(self.bytecode, _globals, _locals)

        for local in _locals:
            self.locals[local] = np.clip(_locals[local], -1, 1)

        self.output[:] = np.clip(self.output[:], 0, 1)

        return _locals
