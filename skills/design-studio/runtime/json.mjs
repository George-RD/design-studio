// JSON.parse validates syntax first. This small lexical pass only rejects duplicate
// keys, including escaped spellings, instead of silently choosing the last value.
export function parseStrictJson(json) {
  const value = JSON.parse(json);
  const lexemes = json.match(/"(?:\\.|[^"\\])*"|[{}\[\]:,]/g) ?? [];
  const stack = [];
  for (let i = 0; i < lexemes.length; i += 1) {
    const item = lexemes[i];
    if (item === '{' || item === '[') stack.push(item === '{' ? new Set() : null);
    else if (item === '}' || item === ']') stack.pop();
    else if (item.startsWith('"') && lexemes[i + 1] === ':') {
      const key = JSON.parse(item);
      if (stack.at(-1)?.has(key)) throw new SyntaxError(`duplicate JSON key: ${key}`);
      stack.at(-1)?.add(key);
    }
  }
  return value;
}
