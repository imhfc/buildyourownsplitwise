---
name: ast-grep
description: 使用 AST 模式進行結構化代碼搜尋。 Use when searching for class definitions, method calls, architecture validation, or any precise code pattern matching using ast-grep.
allowed-tools: [Bash, Read, Glob, Grep]
---

# ast-grep Code Search

Translate natural language to ast-grep rules for AST-based structural code search.


## 觸發與路由


**DO NOT trigger for:**
- 「一般文字搜尋」 → 使用 Grep 工具
- 「審查代碼」 → 使用 review-code

##  工具檢查（自動執行）

**在執行任何 ast-grep 指令前，必須先檢查工具是否已安裝**：

```bash
# 檢查 ast-grep 是否已安裝，如未安裝則提示安裝
bash .claude/skills/shared/check-tool.sh ast-grep
```

若檢查失敗（exit code 1），應：
1. 等待用戶安裝完成
2. 或提供替代方案（如使用 Grep 工具）

**安裝指令**：
```bash
npm install -g @ast-grep/cli
```

## Workflow

1. **Check Tool**: 自動檢查 ast-grep 可用性（見上方）
2. **Clarify Query**: Identify target pattern, language, edge cases
3. **Test Rule**: Create example code → Write rule → Test with `--stdin`
4. **Search**: Use `run` (simple patterns) or `scan` (complex rules)

## Critical Requirements

**IMPORTANT**: The `--lang` (or `-l`) parameter is REQUIRED for all ast-grep commands and must include a language value:

**Correct**:
```bash
ast-grep --pattern '$PATTERN' --lang java src/
ast-grep --pattern '$PATTERN' -l java src/
```

**Wrong** (missing language value):
```bash
ast-grep --pattern '$PATTERN' -l          # ERROR: requires value
ast-grep --pattern '$PATTERN' src/        # ERROR: missing --lang
```

**Supported languages**: java, javascript, typescript, python, rust, go, etc.
(Full list: https://ast-grep.github.io/reference/languages.html)

## Core Commands

### Debug AST Structure
```bash
ast-grep run --pattern 'code' --lang javascript --debug-query=cst
```
Use to find correct `kind` values and understand node structure.

### Test with stdin
```bash
echo "code" | ast-grep scan --inline-rules "id: test
language: javascript
rule:
  pattern: \$PATTERN" --stdin
```

### Search Patterns (simple)
```bash
ast-grep run --pattern 'console.log($ARG)' --lang javascript .
```

### Search Rules (complex)
```bash
ast-grep scan --inline-rules "id: find-async
language: javascript
rule:
  kind: function_declaration
  has:
    pattern: await \$EXPR
    stopBy: end" /path/to/project
```

## Rule Syntax

**Critical**: Always use `stopBy: end` for relational rules (`has`, `inside`)

**Pattern Types**:
- `pattern`: Simple matching (`console.log($ARG)`)
- `kind + has/inside`: Structural matching (function containing await)
- `all/any/not`: Composite logic

**Escape `$` in shell**: Use `\$VAR` or single quotes

**Example Rule**:
```yaml
id: async-no-error
language: javascript
rule:
  all:
    - kind: function_declaration
    - has: {pattern: await $EXPR, stopBy: end}
    - not: {has: {pattern: try { $$$ }, stopBy: end}}
```

## Java Examples (Spring Boot 3)

### Find Spring annotations
```bash
# Find @Service classes
ast-grep run --pattern '@Service' --lang java src/main/java

# Find @Autowired fields
ast-grep run --pattern '@Autowired' --lang java src/main/java

# Find @Transactional methods
ast-grep run --pattern '@Transactional' --lang java src/main/java
```

### Find method calls
```bash
# Find specific method calls (e.g., Mapper.toEntity)
ast-grep run --pattern '\$OBJ.toEntity(\$\$\$)' --lang java src/main/java

# Find repository calls
ast-grep run --pattern '\$REPO.findById(\$\$\$)' --lang java src/main/java

# Find Logger usage
ast-grep run --pattern 'log.info(\$\$\$)' --lang java src/main/java
```

### Find class patterns
```bash
# Find classes by name pattern (using kind for structure)
ast-grep scan --inline-rules "id: service-classes
language: java
rule:
  all:
    - kind: class_declaration
    - regex: 'Service$'" src/main/java

# Find classes with specific annotation
ast-grep scan --inline-rules "id: service-annotated
language: java
rule:
  all:
    - kind: class_declaration
    - has: {pattern: '@Service', stopBy: end}" src/main/java
```

### Architecture validation examples
```bash
# Find private fields (useful for dependency checks)
ast-grep run --pattern 'private' --lang java src/main/java | grep -E 'Accessor|Mapper|Repository'

# Find public methods (for layer compliance checks)
ast-grep run --pattern 'public \$TYPE \$METHOD(\$\$\$)' --lang java src/main/java/**/domain

# Find field injections vs constructor injection
ast-grep run --pattern '@Autowired' --lang java src/main/java
```

### Practical refactoring queries
```bash
# Find all usages of a specific class
ast-grep run --pattern 'new CustomerService(\$\$\$)' --lang java src/

# Find method declarations to understand API surface
ast-grep run --pattern 'public \$TYPE \$METHOD(\$\$\$)' --lang java src/main/java/**/service

# Find deprecated usages
ast-grep run --pattern '@Deprecated' --lang java src/
```

## When to Use ast-grep vs Grep

| Scenario | Tool | Example |
|----------|------|---------|
| Simple string search | Grep | `grep -r "CustomerService" src/` |
| File name patterns | Glob | `**/*Service.java` |
| AST structure search | ast-grep | Find @Service without constructor |
| Architecture validation | ast-grep | Cross-layer dependency check |
| Refactoring impact | ast-grep | Method call pattern analysis |

## Debugging

No matches? Check:
1. `--debug-query=cst` for AST structure
2. Add `stopBy: end` to relational rules
3. Verify `kind` values match language
4. Simplify rule, test incrementally

## Resources

- `references/rule_reference.md`: Full rule syntax reference (load when needed)
