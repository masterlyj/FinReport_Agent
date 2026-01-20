# `src/template/` 开发者备忘录

## 1. 模块定义
**一句话**: 报告模板资源目录，包含Word样式模板和Markdown大纲模板。

**核心文件**:
- `report_template.docx`: Pandoc引用的Word样式模板(字体/页边距/标题样式)
- `company_outline_zh.md`: 公司研究报告大纲模板(中文)
- `company_outline.md`: 公司研究报告大纲模板(英文)
- `industry_outline_zh.md`: 行业研究报告大纲模板

## 2. 使用方式

**在my_config.yaml中配置**:
```yaml
reference_doc_path: 'src/template/report_template.docx'
outline_template_path: 'src/template/company_outline_zh.md'
```

**Pandoc调用**:
```bash
pandoc input.md -o output.docx --reference-doc=report_template.docx
```

## 3. 修改指南

**修改Word样式**:
1. 用MS Word打开`report_template.docx`
2. 修改"标题1"、"标题2"、"正文"等样式
3. 保存后Pandoc会应用这些样式

**修改大纲模板**:
- 直接编辑Markdown文件
- LLM会参考此大纲生成报告结构
- 支持变量占位符(通过Prompt传入)
