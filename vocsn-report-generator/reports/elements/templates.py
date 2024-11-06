#!/usr/bin/env python
"""
These functions override ReportLab functions to extend or customize functionality.

    Version Notes:
        1.0.0.0 - 09/09/2019 - Created with FormattedPage class.
        1.0.0.1 - 11/01/2019 - Swapped report name for device serial number in lower left corner with PHI disabled.
        1.0.0.2 - 11/27/2019 - Disabled footer on cover page.
        1.0.1.0 - 12/12/2019 - Reworked section name management.
        1.0.2.0 - 12/13/2019 - Added Bookmark class to facilitate linking.
        1.0.2.1 - 12/14/2019 - Modified TitleTable to be compatible with multi-builds.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.2.1"

# ReportLab libraries
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import ActionFlowable
from reportlab.platypus import Table, BaseDocTemplate, PageTemplate

# VOCSN modules
from modules.models.report import Report
from reports.elements import footers as foot
from modules.models.vocsn_data import VOCSNData as Data


class FormattedPage(Canvas):
    """ Extend default Canvas class. Overrides canvas operations and includes overlays for all pages in the document.
    This allows access to the total number of pages across entire report from all sections. """

    def __init__(self, *args, **kwargs):
        """ Extend initialization to include var to reference all pages. """
        Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []
        self.vocsn_report = None
        self.vocsn_data = None

    def showPage(self):
        """ Extend page render to add headers and footers. """

        # Initialize page and build counts
        report = self.vocsn_report
        if not hasattr(report, "build_pass"):
            report.pages = 0
            report.build_pass = 0

        # Count build passes and pages
        if self._pageNumber == 1:
            report.build_pass += 1
        if report.build_pass == 1:
            report.pages += 1

        # Add headers and footers with page counts
        if report.build_pass > 1:
            if self._pageNumber > 1:
                self.draw_header()
            self.draw_footer(report.pages)

        # Perform actual page processing
        Canvas.showPage(self)

    def draw_header(self):
        """ Define footer. """
        pass

    def draw_footer(self, page_count: int):
        """ Define footer. """
        if self._pageNumber != 1:
            foot.name_sn(self, self.vocsn_data, self.vocsn_report)
            foot.page(self, self._pageNumber, page_count)


class SectionTemplate(PageTemplate):
    """ Add section name to page template. """

    def __init__(self, *args, section: str, bottom_link: str = None, **kw):
        """ Modify base page template to store section names. """

        # Extend existing constructor
        super(SectionTemplate, self).__init__(*args, **kw)

        # Store section name
        self.section = section
        self.first_page = True
        self.bottom_link = bottom_link
        self.counter = 0

    def attachToPageTemplate(self, pt):
        if pt.onPage:
            def onPage(canv, doc, oop=pt.onPage):
                self.onPage(canv, doc, self.section, self.bottom_link)
                oop(canv, doc)
        else:
            def onPage(canv, doc):
                self.onPage(canv, doc, self.section, self.bottom_link)
        pt.onPage = onPage
        if pt.onPageEnd:
            def onPageEnd(canv, doc, oop=pt.onPageEnd):
                self.onPageEnd(canv, doc)
                oop(canv, doc)
        else:
            def onPageEnd(canv, doc):
                self.onPageEnd(canv, doc)
        pt.onPageEnd = onPageEnd


class CustomBaseDocTemplate(BaseDocTemplate):
    """ Add the ability to pass data object references around within the document creation process. """

    def __init__(self, filename: str, report: Report, data: Data, **kw):
        """ Modify base document to store references to VOCSN data objects. """

        # Extend existing constructor
        super(CustomBaseDocTemplate, self).__init__(filename, **kw)

        # Custom fields
        self.vocsn_report = report
        self.vocsn_data = data
        self.passes = 0

    def _makeCanvas(self, filename=None, canvasmaker=FormattedPage):
        """ Modify _makeCanvas method to pass VOCSN data object references. """

        # Extend existing constructor
        canvas = super()._makeCanvas(filename, canvasmaker)
        canvas.vocsn_report = self.vocsn_report
        canvas.vocsn_data = self.vocsn_data
        return canvas

    def handle_pageBegin(self):
        """Perform actions required at beginning of page.
        shouldn't normally be called directly"""
        self.page += 1
        if self._debug: logger.debug("beginning page %d" % self.page)
        self.pageTemplate.beforeDrawPage(self.canv,self)
        self.pageTemplate.checkPageSize(self.canv,self)
        if type(self.pageTemplate) is SectionTemplate:
            self.pageTemplate.onPage(self.canv, self, name=self.pageTemplate.section,
                                     bottom_link=self.pageTemplate.bottom_link)
        else:
            self.pageTemplate.onPage(self.canv,self)
        for f in self.pageTemplate.frames: f._reset()
        self.beforePage()
        #keep a count of flowables added to this page.  zero indicates bad stuff
        self._curPageFlowableCount = 0
        if hasattr(self,'_nextFrameIndex'):
            del self._nextFrameIndex
        self.frame = self.pageTemplate.frames[0]
        self.frame._debug = self._debug
        self.handle_frameBegin(pageTopFlowables=self._pageTopFlowables)

    def afterFlowable(self, flowable):
        if hasattr(flowable, "bookmark"):
            key = flowable.bookmark
            self.canv.bookmarkPage(key)

    def multiBuild(self, story,
                   maxPasses = 10,
                   **buildKwds
                   ):
        """Makes multiple passes until all indexing flowables
        are happy.

        Override to capture pass number.

        Returns number of passes"""
        self._indexingFlowables = []
        #scan the story and keep a copy
        for thing in story:
            if thing.isIndexing():
                self._indexingFlowables.append(thing)

        #better fix for filename is a 'file' problem
        self._doSave = 0
        self.passes = 0
        mbe = []
        self._multiBuildEdits = mbe.append
        while 1:
            self.passes += 1
            if self._onProgress:
                self._onProgress('PASS', self.passes)
            # if verbose: sys.stdout.write('building pass '+str(passes) + '...')

            for fl in self._indexingFlowables:
                fl.beforeBuild()

            # work with a copy of the story, since it is consumed
            tempStory = story[:]
            self.build(tempStory, **buildKwds)
            #self.notify('debug',None)

            for fl in self._indexingFlowables:
                fl.afterBuild()

            happy = self._allSatisfied()

            if happy:
                self._doSave = 0
                self.canv.save()
                break
            if self.passes > maxPasses:
                raise IndexError("Index entries not resolved after %d passes" % maxPasses)

            #work through any edits
            while mbe:
                e = mbe.pop(0)
                e[0](*e[1:])

        del self._multiBuildEdits
        # if verbose: print('saved')
        return self.passes


class Bookmark(ActionFlowable):
    """ Bookmark class that is flagged as indexing. """

    def __init__(self, key: str):
        """ Instantiate bookmark. """

        # Extend existing constructor
        super(Bookmark, self).__init__()

        # Store bookmark key
        self.bookmark = key
        self.build_count = 0
        self.offset = 0

    def isIndexing(self):
        return True

    def beforeBuild(self):
        return

    def apply(self, doc: CustomBaseDocTemplate):
        """ Applies bookmark. """

        # Count builds
        self.build_count += 1

        # Render bookmark
        if self.build_count > 1:
            canvas = doc.canv
            if self.offset:
                canvas.bookmarkPage(self.bookmark, fit="FitH", top=-self.offset)
            else:
                canvas.bookmarkPage(self.bookmark)

    def draw(self):
        return

    def afterBuild(self):
        return

    def isSatisfied(self):
        return self.build_count > 1


class TrendTable(Table):
    """ Trend table uses custom functions to get absolute position of elements to draw links. """

    def __init__(self, *args, **kw):
        """ Instantiate bookmark. """

        # Extend existing constructor
        super(TrendTable, self).__init__(*args, **kw)

    def drawOn(self, canvas, x, y, _sW=0):
        """ Render final links on main canvas that align with cell blocks. """

        # Call default drawOn function
        Table.drawOn(self, canvas, x, y, _sW)

        # Draw links
        if hasattr(canvas, "blocks_with_links"):
            for block in canvas.blocks_with_links:
                position = (
                    x + block.table_x,
                    y + block.table_y,
                    x + block.table_x + block.size[0],
                    y + block.table_y + block.size[1]
                )
                if block.link:
                    canvas.linkAbsolute(block.title, block.link, position)
