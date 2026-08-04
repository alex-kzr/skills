---
name: open-api-html-to-json-extractor
description: Extract Swagger/OpenAPI JSON from a Swagger UI HTML page. Use when the user provides an HTML file exported from Swagger UI and asks to extract openapi.json or recover the API contract.
---

# open-api-html-to-json-extractor (skill)

## Purpose

Extract an OpenAPI/Swagger specification from an exported Swagger UI HTML page.

Use this skill when the user provides an HTML file that looks like Swagger UI and asks to:
- extract swagger/openapi data;
- get `openapi.json`;
- recover API contract from HTML;
- parse embedded Swagger UI data.

## Input

Expected input: an HTML file containing Swagger UI.

The common supported case is when the OpenAPI spec is embedded in:

```html
<script id="swagger-data" type="application/json">
  ...
</script>
```

Inside this JSON there is usually a `spec` field containing the OpenAPI document.

## Output

Produce an `openapi.json` file with the extracted OpenAPI specification.

Optionally, print a short summary:
- OpenAPI version;
- title;
- number of paths;
- number of schemas.

## Steps

1. Read the HTML file as UTF-8.
2. Find the script block:

   ```html
   <script id="swagger-data" type="application/json">...</script>
   ```

3. HTML-unescape its content.
4. Parse it as JSON.
5. If the parsed object contains `spec`, use `data["spec"]`.
6. Otherwise, if the parsed object itself looks like OpenAPI/Swagger, use it directly.
7. Save the result as formatted JSON.

## Command

```bash
python scripts/extract_swagger_from_html.py input.html openapi.json
```

## Notes

If the script cannot find `swagger-data`, check the HTML for other Swagger initialization patterns, for example:

```js
SwaggerUIBundle({
  url: ".../openapi.json"
})
```

or:

```js
SwaggerUIBundle({
  spec: {...}
})
```

In that case, extract the `url` or embedded `spec` manually or extend the script.
