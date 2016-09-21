__author__ = 'Bones'

from entrez_query import entrez_query
import time
from lxml import etree
import textwrap


#TODO 1: В классе должна быть возможность
#TODO    по данному ID возвращать объект в
#TODO    котором будут атрибуты:
#TODO    а) название статьи
#TODO    б) библиография
#TODO    в) авторы
#TODO    г) текст абстракта
#TODO    д) статус OA/NonOA,
#TODO       если ОA то ссылка
#TODO 2: Реализована функция скидывания запроса
#TODO    в базу данных - под вопросом

class pubmed(entrez_query):

    utility = "efetch"
    def __init__(self, query,*args,**kwargs):
        super().__init__(query, **kwargs)


#==========>Methods <====================

    def obtain_data(self, gap=100):
        total = self.total_ids()
        print("Total ids in query: {0}".format(total))
        start = 0
        condition = True

        print("processing started")

        while condition == True:

            if start+gap < total:
                print("requesting ids from {0} up to {1}".format(start, start+gap))
            else:
                print("requesting ids from {0} up to {1}".format(start, total))

            chunk = self.request_ids(start = start, gap = gap)

            print("ids received")

            access_string = ','.join(self.id_list[start:start+gap])
            time.sleep(0.3)
            
            if start == 0:
                print("fetching...")
            else:
                print("fetching next chunk...")
                
            fetch_adress = self.fetch_adress(access_string)

            self.fetch(fetch_adress)

            print("chunk processing finished\n")

            start += gap
            if start > total:
                condition = False

        print("ids processed: {0}\n".format(len(self.id_list)))

    def fetch_adress(self, ids_string):
        adress = self.BASE + "efetch.fcgi?" + self.db + "&id=" + ids_string + "&retmode=xml"
        return adress

    def fetch(self, adress):
        tree = self.return_tree(adress)
        print("data received, starting parser...")
        for node in tree.findall("PubmedArticle"):
            subnode = node.find("MedlineCitation")
            MedlineCitationTree = etree.ElementTree(subnode)

            #PMID
            pmid = MedlineCitationTree.find("PMID").text

            #Bibliography
            self.Bibliography(pmid, MedlineCitationTree)

            #Title
            self.Title(pmid, MedlineCitationTree)

            #Abstract
            self.Abstract(pmid, MedlineCitationTree)

            #AuthorsList
            self.AuthorsList(pmid, MedlineCitationTree)

            #Keywords
            self.Keywords(pmid, MedlineCitationTree)

            #MeSH headings
            self.MeSH_Headings(pmid, MedlineCitationTree)

    def dump_to_db(self):
        pass

    def dump_to_file(self, filename = "dump.txt"):
        with open(filename, "w", encoding='utf-8') as dump:
            print("Query: {0}\n".format(self.query), file=dump)
            print("Number of records: {0}\n".format(len(self.id_list)), file=dump)
            print("".join("=" for i in range(71)), file=dump)
            print("\n\n", file=dump)
            try:
                for key in self.id_list:
                    title = textwrap.dedent(self.__Article_Title[key]).strip()
                    print("{0}\n".format(textwrap.fill(title)), file=dump)

                    authors = textwrap.dedent(self.__Article_Authors[key]).strip()
                    print("{0}\n".format(textwrap.fill(authors)), file=dump)

                    print("PBMID: {0}\n".format(key), file=dump)

                    bibliography = textwrap.dedent(self.__Article_Bibliography[key]).strip()
                    print("{0}\n".format(textwrap.fill(bibliography)), file=dump)

                    abstract = textwrap.dedent(self.__Article_Abstract[key]).strip()
                    print("{0}\n\n\n".format(textwrap.fill(abstract, initial_indent='   ', subsequent_indent='')), file=dump)
            except:
                print("dumping failed")
#==========>Inner helper functions<==========

    def AuthorsList(self, ID, tree):
        try:
            AuthorList = tree.find("//AuthorList")
            AuthorList = etree.ElementTree(AuthorList)
            Authors = []
            for author in AuthorList.iterfind("Author"):
                    try:
                        LastName = author.findtext("LastName")
                        Initials = author.findtext("Initials")
                        Authors.append(LastName + ", " + Initials)
                    except:
                        pass
            Authors = "; ".join(Authors)
        except:
            Authors = "[not available]"

        self.a_authors(ID, Authors)

    def Abstract(self, ID, tree):
        try:
            Abstract = tree.find("//Abstract")
            Abstract = etree.ElementTree(Abstract)
            Abstract = Abstract.find("//AbstractText").text
        except:
            Abstract = "[not available]"

        self.a_abstract(ID, Abstract)

    def Title(self, ID, tree):
        try:
            ArticleTitle = tree.find("//ArticleTitle").text
        except:
            ArticleTitle = "[not available]"

        self.a_title(ID, ArticleTitle)

    def Bibliography(self, ID, tree):
        Journal = tree.find("//Journal")
        Journal = etree.ElementTree(Journal)

        try:
            vol = Journal.find("//Volume").text
        except:
            vol = ""
        try:
            issue = Journal.find("//Issue").text
        except:
            issue = ""
        try:
            year = Journal.find("//Year").text
        except:
            year = ""
        try:
            month = Journal.find("//Month").text
        except:
            month = ""
        try:
            day = Journal.find("//Day").text
        except:
            day = ""
        try:
            Jtitle = Journal.find("//Title").text
        except:
            Jtitle = ""
        try:
            pagination = tree.find("//Pagination").text
            pagination = pagination.strip(' \t\n\r')
        except:
            pagination = ""

        if issue != "":
            issue = "("+ issue + ")"

        if pagination != "":
            pagination = ": " + pagination

        if day == "":
            if month == "":
                year = year + ";"
            else:
                month = month + ";"
        else:
            day = day + ";"

        date = (year + " " + month + " " + day).strip(' \t\n\r')

        bibliography_summ = (Jtitle + ", " + date + " " + vol + issue + pagination).strip(' \t\n\r')

        self.a_bibliography(ID, bibliography_summ)

    def Keywords(self, ID, tree):
        KeywordList = []
        try:
            Keywords = tree.find("//KeywordList")
            for keyword in Keywords.getchildren():
                KeywordList.append(keyword.text)
            self.a_keywords(ID, KeywordList)
        except Exception as Exp:
            print("Error in keywords request in PMID: {0}".format(ID))
            self.a_keywords(ID, KeywordList)

    def MeSH_Headings(self, ID, tree):
        KeywordList = []
        try:
            MeSH_root = tree.find("//MeshHeadingList")
            for item in MeSH_root.iter():
                if item.tag == "DescriptorName":
                    KeywordList.append(item.text)
            self.a_mesh_headings(ID, KeywordList)

        except Exception as Exp:
            #print(Exp)
            print('Error in MeSH headings request in PMID: {0}'.format(ID))
            self.a_mesh_headings(ID, '[not available]')

    def Whats_Keywords(self, ID):
        return self.__Article_Keywords[ID]

    def Whats_MeSH(self, ID):
        return self.__Article_MeSH[ID]

    def a_title(self, ID, value):
        try:
            self.__Article_Title.update({ID:value})
        except:
            self.__Article_Title = {ID:value}

    def a_bibliography(self, ID, value):
        try:
            self.__Article_Bibliography.update({ID:value})
        except:
            self.__Article_Bibliography = {ID:value}

    def a_authors(self, ID, value):
        try:
            self.__Article_Authors.update({ID:value})
        except:
            self.__Article_Authors = {ID:value}

    def a_abstract(self, ID, value):
        try:
            self.__Article_Abstract.update({ID:value})
        except:
            self.__Article_Abstract = {ID:value}

    def a_keywords(self, ID, value):
        try:
            self.__Article_Keywords.update({ID:value})
        except:
            self.__Article_Keywords = {ID:value}

    def a_mesh_headings(self, ID, value):
        try:
            self.__Article_MeSH.update({ID:value})
        except:
            self.__Article_MeSH = {ID:value}

if __name__ == "__main__":
    query = open("test_query.txt","r")
    query = query.read()
    papers = pubmed(query)
    papers.obtain_data()
    ID = papers.id_list[0]
    print(ID, papers.Whats_Keywords(ID))
    print(ID, papers.Whats_MeSH(ID))
