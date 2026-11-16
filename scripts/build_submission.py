"""Build the academic Word report from the shared research narrative.

Use a Python environment with python-docx installed. This presentation-only
builder is separate from the scientific analysis dependencies.
"""
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from report_content import ROOT, OUT, TITLE, SUBTITLE, AUTHOR, DATE, REPO, SITE, get_sections, REFERENCES


def hyperlink(paragraph, text, url):
    rel=paragraph.part.relate_to(url,RT.HYPERLINK,is_external=True)
    link=OxmlElement('w:hyperlink');link.set(qn('r:id'),rel)
    run=OxmlElement('w:r');props=OxmlElement('w:rPr')
    color=OxmlElement('w:color');color.set(qn('w:val'),'164B62');props.append(color)
    run.append(props);t=OxmlElement('w:t');t.text=text;run.append(t);link.append(run);paragraph._p.append(link)


def make_report():
    doc=Document();sec=doc.sections[0]
    sec.page_width=Inches(8.5);sec.page_height=Inches(11)
    sec.top_margin=sec.bottom_margin=Inches(.8)
    sec.left_margin=sec.right_margin=Inches(.9)
    styles=doc.styles
    for name in ['Normal','Title','Subtitle','Heading 1','Heading 2','Heading 3','Caption']:
        st=styles[name];st.font.name='Times New Roman';st.font.color.rgb=RGBColor(0,0,0)
    normal=styles['Normal'];normal.font.size=Pt(11.5)
    normal.paragraph_format.space_after=Pt(7)
    normal.paragraph_format.line_spacing=1.12
    for name,size in [('Title',23),('Subtitle',13),('Heading 1',16),('Heading 2',12.5)]:
        st=styles[name];st.font.size=Pt(size)
        st.paragraph_format.space_before=Pt(15 if name.startswith('Heading') else 0)
        st.paragraph_format.space_after=Pt(8)
        st.paragraph_format.keep_with_next=True
        if name.startswith('Heading'): st.font.bold=True
    styles['Caption'].font.size=Pt(9.5)
    styles['Caption'].font.bold=False
    styles['Caption'].paragraph_format.space_after=Pt(9)
    # Remove template borders and theme fonts so explicit academic styles prevail.
    for element in [doc.styles.element, doc.element]:
        for border in list(element.iter(qn('w:pBdr'))): border.getparent().remove(border)
        for fonts in element.iter(qn('w:rFonts')):
            for attr in ['asciiTheme','hAnsiTheme','eastAsiaTheme','cstheme']:
                fonts.attrib.pop(qn('w:'+attr),None)
    doc.core_properties.title=TITLE;doc.core_properties.subject=SUBTITLE
    doc.core_properties.author=AUTHOR
    doc.core_properties.keywords='Philadelphia; pharmacies; accessibility; travel; emissions; spatial analysis'
    doc.add_paragraph(TITLE,'Title');doc.add_paragraph(SUBTITLE,'Subtitle')
    p=doc.add_paragraph(f'{AUTHOR}\nUniversity of Pennsylvania\n{DATE}')
    p.paragraph_format.space_after=Pt(14)
    for i,section in enumerate(get_sections()):
        head=doc.add_heading(section['title'],1)
        if section['id']=='introduction': head.paragraph_format.page_break_before=True
        for b in section['blocks']:
            if b['type']=='p': doc.add_paragraph(b['text'])
            elif b['type']=='h3': doc.add_heading(b['text'],2)
            elif b['type']=='list':
                for n,text in enumerate(b['items'],1):
                    p=doc.add_paragraph(f'{n}. {text}')
                    p.paragraph_format.left_indent=Inches(.17)
                    p.paragraph_format.first_line_indent=Inches(-.17)
            elif b['type']=='figure':
                p=doc.add_paragraph();p.paragraph_format.keep_with_next=True
                run=p.add_run();run.add_picture(str(OUT/b['file']),width=Inches(6.7))
                run._r.xpath('.//wp:docPr')[0].set('descr',b['alt'])
                doc.add_paragraph(b['caption'],'Caption')
            elif b['type']=='table':
                p=doc.add_paragraph(b['caption'],'Caption');p.paragraph_format.keep_with_next=True
                table=doc.add_table(rows=1,cols=len(b['headers']));table.autofit=False
                table.alignment=WD_TABLE_ALIGNMENT.CENTER
                widths=b['widths'] or [1/len(b['headers'])]*len(b['headers'])
                for j,w in enumerate(widths):table.columns[j].width=Inches(6.7*w)
                rows=[b['headers']]+b['rows']
                for ri,data in enumerate(rows):
                    row=table.rows[0] if ri==0 else table.add_row()
                    trpr=row._tr.get_or_add_trPr();cant=OxmlElement('w:cantSplit');trpr.append(cant)
                    if ri==0:
                        repeat=OxmlElement('w:tblHeader');trpr.append(repeat)
                    for j,text in enumerate(data):
                        cell=row.cells[j];cell.width=Inches(6.7*widths[j]);cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
                        tcpr=cell._tc.get_or_add_tcPr()
                        borders=OxmlElement('w:tcBorders')
                        for edge in ['top','left','bottom','right']:
                            e=OxmlElement('w:'+edge);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'D9D9D9');borders.append(e)
                        tcpr.append(borders)
                        margins=OxmlElement('w:tcMar')
                        for edge in ['top','left','bottom','right']:
                            e=OxmlElement('w:'+edge);e.set(qn('w:w'),'95');e.set(qn('w:type'),'dxa');margins.append(e)
                        tcpr.append(margins)
                        shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'E7EDF2' if ri==0 else 'FFFFFF');tcpr.append(shade)
                        p=cell.paragraphs[0];p.paragraph_format.space_after=Pt(0);p.paragraph_format.line_spacing=1.05
                        if len(rows)<=4: p.paragraph_format.keep_with_next=(ri<len(rows)-1)
                        if j>0 and all(c in '0123456789.,- ' for c in str(text)):p.alignment=WD_ALIGN_PARAGRAPH.CENTER
                        r=p.add_run(str(text));r.font.size=Pt(10.2);r.bold=(ri==0)
                p=doc.add_paragraph();p.paragraph_format.space_after=Pt(1);p.paragraph_format.line_spacing=.3;p.add_run().font.size=Pt(3)
    doc.add_heading('References',1).paragraph_format.page_break_before=True
    for n,(label,url) in enumerate(REFERENCES,1):
        p=doc.add_paragraph(f'[{n}] {label} ');hyperlink(p,'Source',url)
        p.paragraph_format.space_after=Pt(10)
    doc.add_heading('Research records',2)
    p=doc.add_paragraph('Website: ');hyperlink(p,SITE,SITE)
    p=doc.add_paragraph('Code, notebooks, data provenance and detailed protocol: ');hyperlink(p,'GitHub research repository',REPO)
    p=doc.add_paragraph('Public analytical inputs were retrieved on 16 November 2026. The repository source manifest records exact retrieval times and file checksums. The downloadable package contains the cached public analytical inputs required to reproduce the spatial assessment.')
    p=sec.footer.paragraphs[0];p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    r=p.add_run();field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');r._r.addnext(field)
    path=OUT/'Pharmacy_Access_Research_Report.docx';doc.save(path);print(path)

if __name__=='__main__':make_report()
