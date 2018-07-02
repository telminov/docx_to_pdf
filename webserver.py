import asyncio
from aiohttp import web
import aiofiles
import tempfile
import json
import shutil
import os

LIBRE_OFFICE_PATH = '/usr/lib/libreoffice/program/soffice'


class DocxToPdf(web.View):

    async def post(self):
        tmp_path = tempfile.mkdtemp(dir='/tmp/')
        try:
            tmp_path_docx = tmp_path + '/target.docx'
            tmp_path_pdf = tmp_path + '/target.pdf'

            data = await self.request.post()
            if 'docx' not in data:
                return web.Response(
                    text=json.dumps({'error': 'Expecting POST-parameter "docx" with target file.'}),
                    status=400,
                    headers={'Content-Type': 'application/json'}
                )

            filename = '.'.join(data['docx'].filename.split('.')[:-1])  # filename without extension
            docx_file = data['docx'].file

            content = docx_file.read()
            async with aiofiles.open(tmp_path_docx, 'wb') as f:
                await f.write(content)

            cmd = '%s --headless --convert-to pdf --outdir %s %s' % (
                LIBRE_OFFICE_PATH, tmp_path, tmp_path_docx
            )
            p = await asyncio.create_subprocess_shell(cmd=cmd)
            result_code = await p.wait()
            if result_code > 0:
                return web.Response(
                    text=json.dumps({'error': 'Error of converting docx to pdf'}),
                    status=500,
                    headers={'Content-Type': 'application/json'}
                )

            async with aiofiles.open(tmp_path_pdf, 'rb') as f:
                pdf_data = await f.read()

            headers = {
                'Content-Type': 'application/pdf',
                'Content-Disposition': 'filename=%s.pdf' % filename,
            }
            return web.Response(body=pdf_data, headers=headers)
        finally:
            shutil.rmtree(tmp_path)


class Server:

    @staticmethod
    def run():
        port = int(os.environ.get('DOCX_TO_PDF_POST', 80))

        app = web.Application()
        app.router.add_post('/docx_to_pdf/', DocxToPdf)
        web.run_app(app, port=port)


if __name__ == '__main__':
    Server.run()
