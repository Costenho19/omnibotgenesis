#!/usr/bin/env python3
"""
Generate institutional PDFs for RFC-ATF-2 and RFC-ATF-3.
Uses weasyprint for clean typography.
"""
import re
import hashlib
import os
import sys

# RFC content will be passed as file paths or fetched
RFC_FILES = {
    "RFC-ATF-2": "/tmp/RFC-ATF-2.md",
    "RFC-ATF-3": "/tmp/RFC-ATF-3.md",
}

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  @page {{
    size: A4;
    margin: 2.5cm 2.8cm 2.5cm 2.8cm;
    @top-center {{
      content: "OMNIX QUANTUM OPEN STANDARD — {title_short}";
      font-family: 'Courier New', monospace;
      font-size: 8pt;
      color: #666;
    }}
    @bottom-center {{
      content: "Page " counter(page) " of " counter(pages);
      font-family: 'Courier New', monospace;
      font-size: 8pt;
      color: #666;
    }}
  }}

  body {{
    font-family: 'Courier New', Courier, monospace;
    font-size: 10pt;
    line-height: 1.5;
    color: #1a1a1a;
    background: #fff;
  }}

  .cover {{
    page-break-after: always;
    text-align: center;
    padding-top: 6cm;
  }}

  .cover .org {{
    font-size: 10pt;
    color: #555;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 2cm;
  }}

  .cover h1 {{
    font-size: 16pt;
    font-weight: bold;
    line-height: 1.4;
    margin-bottom: 1cm;
    color: #0a0a0a;
  }}

  .cover .meta {{
    font-size: 9pt;
    color: #555;
    margin-top: 2cm;
    line-height: 2;
  }}

  .cover .doi-block {{
    margin-top: 2cm;
    border: 1px solid #ccc;
    display: inline-block;
    padding: 0.5cm 1cm;
    font-size: 9pt;
    color: #333;
  }}

  pre, code {{
    font-family: 'Courier New', monospace;
    font-size: 9pt;
    white-space: pre-wrap;
    word-wrap: break-word;
  }}

  pre {{
    background: #f8f8f8;
    border-left: 3px solid #ccc;
    padding: 0.4cm;
    margin: 0.3cm 0;
  }}

  h1 {{ font-size: 13pt; margin-top: 1cm; border-bottom: 1px solid #ccc; padding-bottom: 3pt; }}
  h2 {{ font-size: 11pt; margin-top: 0.8cm; }}
  h3 {{ font-size: 10pt; margin-top: 0.5cm; }}

  .toc {{ page-break-after: always; }}
  .toc h2 {{ font-size: 12pt; }}
  .toc ul {{ list-style: none; padding: 0; }}
  .toc li {{ padding: 2pt 0; }}

  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 9pt;
    margin: 0.5cm 0;
  }}
  th {{
    background: #f0f0f0;
    border: 1px solid #ccc;
    padding: 4pt 6pt;
    text-align: left;
    font-weight: bold;
  }}
  td {{
    border: 1px solid #ccc;
    padding: 4pt 6pt;
    vertical-align: top;
  }}

  .invariant {{
    background: #f9f9f9;
    border: 1px solid #e0e0e0;
    padding: 0.3cm 0.5cm;
    margin: 0.3cm 0;
    font-size: 9pt;
  }}

  blockquote {{
    border-left: 3px solid #999;
    margin-left: 0;
    padding-left: 0.5cm;
    color: #444;
    font-style: italic;
  }}

  .watermark-none {{}}
  
  p {{ margin: 0.2cm 0; text-align: justify; }}
</style>
</head>
<body>

<div class="cover">
  <div class="org">OMNIX QUANTUM LTD · Standards Track</div>
  <h1>{title}</h1>
  <div class="meta">
    Version 1.0.0 &nbsp;·&nbsp; Published: May 2026<br>
    Author: Harold Nunes (Ed.)<br>
    Organization: OMNIX QUANTUM LTD<br>
    Category: Standards Track · Open Standard<br>
    License: Creative Commons Attribution 4.0
  </div>
  <div class="doi-block">
    DOI: pending (Zenodo submission in progress)<br>
    GitHub: github.com/Costenho19/atf-protocol-standard
  </div>
</div>

{body}

</body>
</html>
"""

def md_to_html_body(md_text):
    """Convert RFC markdown (monospace format) to clean HTML body."""
    import markdown
    # The RFCs are in RFC-style plain text, not standard markdown
    # We'll treat code blocks and convert headings
    lines = md_text.split('\n')
    html_lines = []
    in_code = False
    in_pre = False
    
    for line in lines:
        # Code fence detection
        if line.strip().startswith('```'):
            if not in_code:
                in_code = True
                html_lines.append('<pre><code>')
            else:
                in_code = False
                html_lines.append('</code></pre>')
            continue
        
        if in_code:
            escaped = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            html_lines.append(escaped)
            continue
        
        # Section headings (all caps lines or numbered sections)
        stripped = line.strip()
        
        # Major section: line that is all caps, standalone
        if (stripped and stripped == stripped.upper() and 
            len(stripped) > 3 and len(stripped) < 60 and
            not stripped.startswith('|') and
            re.match(r'^[A-Z][A-Z0-9 \-\.]+$', stripped)):
            html_lines.append(f'<h2>{stripped.title()}</h2>')
            continue
        
        # Numbered section headings like "1.  Introduction" 
        m = re.match(r'^(\d+(?:\.\d+)*)\.\s{2,}(.+)$', stripped)
        if m:
            num = m.group(1)
            title = m.group(2)
            depth = num.count('.') + 1
            tag = f'h{min(depth+1, 4)}'
            html_lines.append(f'<{tag}>{num}. {title}</{tag}>')
            continue
        
        # Appendix headings
        m2 = re.match(r'^(Appendix [A-Z](?:\.\d+)*)\.\s+(.+)$', stripped)
        if m2:
            html_lines.append(f'<h2>{m2.group(1)}. {m2.group(2)}</h2>')
            continue
        
        # Empty line
        if not stripped:
            html_lines.append('<p></p>')
            continue
        
        # Normal paragraph text
        escaped = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        html_lines.append(f'<p>{escaped}</p>')
    
    return '\n'.join(html_lines)


def generate_pdf(rfc_name, md_path, output_path):
    """Generate institutional PDF from RFC markdown."""
    from weasyprint import HTML, CSS
    
    with open(md_path, 'r') as f:
        md_content = f.read()
    
    # Extract title from content
    title_map = {
        "RFC-ATF-2": "RFC-ATF-2: Agent Trust Fabric\nRuntime Governance Continuity",
        "RFC-ATF-3": "RFC-ATF-3: Agent Trust Fabric\nGovernance Policy Interoperability,\nEvidence Lifecycle, and Forensic Verification Protocol",
    }
    title_short_map = {
        "RFC-ATF-2": "RFC-ATF-2",
        "RFC-ATF-3": "RFC-ATF-3",
    }
    
    body = md_to_html_body(md_content)
    html_content = HTML_TEMPLATE.format(
        title=title_map[rfc_name],
        title_short=title_short_map[rfc_name],
        body=body
    )
    
    # Save HTML for debugging
    html_path = output_path.replace('.pdf', '.html')
    with open(html_path, 'w') as f:
        f.write(html_content)
    
    print(f"  Generating {output_path}...")
    HTML(string=html_content, base_url='/').write_pdf(output_path)
    print(f"  Done: {output_path}")
    return output_path


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


if __name__ == '__main__':
    rfc_name = sys.argv[1] if len(sys.argv) > 1 else "RFC-ATF-2"
    md_path = sys.argv[2] if len(sys.argv) > 2 else RFC_FILES[rfc_name]
    output = sys.argv[3] if len(sys.argv) > 3 else f"/tmp/{rfc_name}-v1.0.0.pdf"
    
    generate_pdf(rfc_name, md_path, output)
    checksum = sha256_file(output)
    size = os.path.getsize(output)
    print(f"\nSHA256: {checksum}")
    print(f"Size:   {size:,} bytes")
    
    # Write checksum file
    checksum_path = output.replace('.pdf', '.SHA256')
    with open(checksum_path, 'w') as f:
        f.write(f"{checksum}  {os.path.basename(output)}\n")
    print(f"Checksum saved: {checksum_path}")
