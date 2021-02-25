import PyPDF2
import tabula
import os
import glob
import pandas as pd
from pdfminer.pdfparser import PDFParser
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LTTextBoxHorizontal
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage

total_debt = [
    'total debt', 'total liabilities'
]

net_income = [
    'net income', 'net loss', 'net (loss) income', 'earnings'
]

occupancy_rate = [
    'occupancy rate'
]

fortum_pdf = 'data/reports/fortum_financials2019_3_0.pdf'
vno_pdf = 'data/reports/91b3d76b-a269-4a59-8d33-de446d78384c.pdf'
frt_pdf = 'data/reports/FRT_2019AnnualReportandProxy_Final.pdf'


def update_directory(analyse):
    company = analyse["ticket"]
    try:
        files = glob.glob(f'tables/{company}/*')
        for f in files:
            os.remove(f)
    except FileNotFoundError:
        pass

    if not os.path.exists(f'tables/{company}'):
        os.makedirs(f'tables/{company}')


def overwrite_dlg(filename):
    ans = input("Overwrite file '%s'? Yes/No [Y/n]: " % filename).lower()
    if ans in ["y", ""]:
        return True

    return False


def pdf_copy(input: str, output: str, pages: [int], yes_to_all=False):
    if not os.path.isfile(input):
        print("Error. The file '%s' does not exist." % input)
        return

    if os.path.isfile(output) and not yes_to_all and not overwrite_dlg(output):
        return

    with open(input, "rb") as inputfile:
        reader = PyPDF2.PdfFileReader(inputfile)
        outputfile = open(output, "wb")
        writer = PyPDF2.PdfFileWriter()
        for pagenr in sorted(pages):
            page = reader.getPage(pagenr)
            writer.addPage(page)
            writer.write(outputfile)
        outputfile.close()


def parse_document(analyse):
    print("has started parse document")
    rsrcmgr = PDFResourceManager()
    device = PDFPageAggregator(rsrcmgr, laparams=LAParams())
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    number = 0
    pages = []
    for page in PDFPage.get_pages(open(analyse['source'], 'rb')):
        number = number + 1
        interpreter.process_page(page)
        layout = device.get_result()
        for element in layout:
            if isinstance(element, LTTextBoxHorizontal):
                for extracted_text in element.get_text().splitlines():
                    extracted_text = extracted_text.lower()
                    if any(text in extracted_text for text in total_debt):
                        pages.append(number)
                    if any(text in extracted_text for text in net_income):
                        pages.append(number)
                    if any(text in extracted_text for text in occupancy_rate):
                        pages.append(number)

    print('pages', set(pages))
    return set(pages)


def grab_tables(pages, analyse):
    print("has started grab tables")
    index = 0
    update_directory(analyse)
    last_page_id = 0
    company = analyse["ticket"]
    print(len(pages))
    for page in pages:
        table = tabula.read_pdf(analyse['source'], encoding='utf-8', pages=page, multiple_tables=True)
        if table:
            if last_page_id == page + 1:
                data = pd.read_csv(f'tables/{company}/data_report_{index}.csv')
                dataframe = pd.concat([data, table[0]])
                dataframe.to_csv(f'tables/{company}/data_report_{index}.csv', encoding='utf-8')
            else:
                table[0].to_csv(f'tables/{company}/data_report_{index}.csv', encoding='utf-8')
                index = index + 1
            last_page_id = page


analyse = {
    'ticket': 'fortum_pdf',
    'source': fortum_pdf
}

pages = parse_document(analyse)
grab_tables(pages, analyse)


