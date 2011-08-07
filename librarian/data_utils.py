from .models import Paper, Person, Journal, Institution, Country, Town, Citation, Authorship, Affiliation, Raw_cit
from django.core.exceptions import ObjectDoesNotExist
from google.appengine.api import taskqueue
import re, datetime


def ISIquery(ran,citedList):
    # ran is the range of citations to extract from citedList. It must be smaller than 16.
    isiquery=""
    for i in ran:
        vec=citedList[i][0].split(', ')
        source=Journal.objects.get(short_name=vec[2].capitalize())
        source=source.name
        if source:
            isiquery+="(AU=(%s) AND PY=(%s) AND SO=(%s))" % (vec[0],vec[1],source)
            isiquery+=" OR "
        else:
            print "record omitted: journal not found " + vec[2]
    isiquery=isiquery[:-4]
    return isiquery

def cleanUnivName(univName):
        if "ETH" in univName:
                univName="ETH"
        elif "Univ Roma" in univName or "Univ Rome" in univName:
		univName="Univ Roma Tre"
        elif "univ Lyon" in univName:
                univName="Univ Lyon"
        elif "Aix Marseille" in univName:
                univName="Univ Aix Marseille"
        elif "Univ Bordeaux" in univName:
                univName="Univ Bordeaux"
        elif "Univ Paris 07" in univName or "Univ Diderot" in univName:
                univName="Univ Paris Diderot"
        elif "Univ Evry" in univName:
                univName="Univ Evry"
        elif "CIGB" in univName:
                univName="Ctr Genet Engn & Biotechnol"
        elif "CSIC" in univName:
                univName="CSIC"
        elif "DNA 2" in univName:
                univName="DNA 20 inc"
        elif "INRIA" in univName:
                univName="INRIA"
        elif "Normale Super" in univName:
                univName="Ecole Normale Super"
        elif "Fdn Appl Mol Evol" in univName:
                univName="Fdn Appl Mol Evol"
        elif "massachusetts gen hosp" in univName.lower():
                univName="Massachusetts Gen Hosp"
        elif "Org Int Dialogue & Conflict Management" in univName:
                univName="Org Int Dialogue & Conflict Management"
        
        return univName


def uniquify_journals():
	journals=Journal.objects.all()
	journals=list(journals)
	journal_names=[j.name for j in journals]
	for name in journal_names:
		q=Journal.objects.filter(name=name)
		q=list(q)
		if len(q)>1:
		#	print name
			short_names=[j.short_name for j in q]
			try: #If one of the short_names is the same as the name, then deletes the other journal entities
				print short_names, name
				ind=short_names.index(name)
				for i in range(len(q)):
					if i!=ind:
						print q[i]
						q[i].delete()
			except:
				for i in range(1,len(q)):
					q[i].delete()

	#Do the same for short_names
	journals=Journal.objects.all()
	journals=list(journals)
	journal_names=[j.short_name for j in journals]
	for short_name in journal_names:
		q=Journal.objects.filter(short_name=short_name)
		q=list(q)
		if len(q)>1:
                        names=[j.name for j in q]
			print names[0], short_name
			for i in range(1,len(q)):
					q[i].delete()
			

def parse_ISI_data2(data):
	months={"jan":1,"feb":2,"mar":3,"apr":4,"may":5,"jun":6,"jul":7,"aug":8,"sep":9,"oct":10,"nov":11,"dec":12}


	PT,AU,BA,ED,GP,AF,CA,TI,SO,SE,LA,DT,CT,CY,CL,SP,HO,DE,ID,AB,C1,RP,EM,FU,FX,CR,NR,TC,PU,PI,PA,SN,BN,DI,J9,JI,PD,PY,VL,IS,PN,SU,SI,BP,EP,AR,DI2,PG,SC,GA,UT = data
	TI=TI.capitalize()

	try:
            paper=Paper.objects.get(title=TI)
        except:
            return 1

        SO=SO.capitalize()
        jour, created=Journal.objects.get_or_create(name=SO)
        if created:
            try:
                jour.get_name() #finds this abbreviated name of the journal (useful to find which citation matches which paper)
            except:
                pass

        paper.journal=jour
        paper.save()
        
	
def parse_ISI_data(data):
	months={"jan":1,"feb":2,"mar":3,"apr":4,"may":5,"jun":6,"jul":7,"aug":8,"sep":9,"oct":10,"nov":11,"dec":12}


	PT,AU,BA,ED,GP,AF,CA,TI,SO,SE,LA,DT,CT,CY,CL,SP,HO,DE,ID,AB,C1,RP,EM,FU,FX,CR,NR,TC,Z9,PU,PI,PA,SN,BN,J9,JI,PD,PY,VL,IS,PN,SU,SI,BP,EP,AR,DI,PG,WC,SC,GA,UT,X = data
	TI=TI.capitalize()
	
	query=Paper.objects.filter(title=TI) #Tests if the paper info was already added to the database
	if C1 and not query:
		auNamesList=[[j.strip() for j in i.split(", ")] for i in AU.split(";")]
	
		############# Journal #############
		SO=SO.capitalize()
		jour, created=Journal.objects.get_or_create(name=SO)
		if created:
		    jour.get_name()
		    #taskqueue.add(url='/librarian/update_journal/',
                    #             params={'pk': jour.pk},
                    #             queue_name="journal")

		############# Pub Date ############
		PM=0
		if PD:
			for m in months.keys():
	       			if m in PD.lower():
	               			PM=months[m]
	                		break
				else: 
					PM=0
	
		
		############# Paper ############
                #checks if a Raw_cit objects corresponding to the paper already exists in the database
                raw_cit=None
                if DI:
                    raw_cit=Raw_cit.objects.filter(doi=DI)
                if not raw_cit:
                    #applies a first set of filter then goes through all the raw_cits to find a good match
                    raw_cit=Raw_cit.objects.filter(last_name=auNamesList[0][0]).filter(jour=jour)
                    raw_cit=list(raw_cit)
                    for cit in raw_cit:
                        if cit.vol:
                            if cit.vol!=VL:
                                raw_cit.remove(cit)
                                continue
                        if cit.year:
                            if cit.year!=int(PY):
                                raw_cit.remove(cit)
                                continue
##                        if cit.page:
##                            if cit.page[1:]!=PN:
##                                raw_cit.remove(cit)
##                                continue

                
                if len(raw_cit)>=1:
                    #if a single match is found update this paper data with the ISI data
                    raw_cit=raw_cit[0] #we chose the first raw_cit in case there are several matches... we should implement something else in this case
                    new_paper=Paper.objects.get(raw_cit=raw_cit)
                    new_paper.title=TI
                    new_paper.journal=jour
                    new_paper.volume=VL
                    new_paper.page=PN
                    new_paper.pubMonth=int(PM)
                    new_paper.pubYear=int(PY)
                    new_paper.abstract=AB
                    new_paper.doi=DI
                    new_paper.raw_citations=CR
                elif len(raw_cit)==0:
                    #create a new Paper object
                    new_paper=Paper(title = TI,
				journal = jour,
				volume = VL,
                                page = PN,
				pubMonth = int(PM),
				pubYear = int(PY),
				abstract=AB,
				doi=DI,
				raw_citations=CR,
                                sbw=0,
				)
		
		new_paper.added=datetime.datetime.now()
                new_paper.save()
	
	
		############## Authors - Affiliations ####################
		counted_au=[] #used not to count authors twice when they have several affiliations for a same paper
		corres_au=RP.split(",")[0]
		if "[" in C1:
		        affs=C1[1:].split("; [")
		elif  ";" in C1: #in this case, there are several affiliations but we don't know who belongs to what institution.
		#Neverthless in many cases the different institutions are just different departemnts of the same institution, so we check for this
		        affs=[[i.strip() for i in x.split(",")] for x in C1.split(";")]
		        sameInst=1
		        for aff in affs[1:]:
		                if aff[0]!=affs[0][0]:
		                        sameInst=0
		        
		        if sameInst:
		                affs=[", ".join(affs[-1])]
		        
		else:
		        affs=[C1]
		
		for aff in affs:
                        if "[" not in C1 and len(affs)>1:
		                #in this case we do not know which authors belong to which affiliation
		                na_country, created=Country.objects.get_or_create(name="N.A",has_SB=True,sbw=0)
		                current_inst, created=Institution.objects.get_or_create(name="N.A",country=na_country)
		                auNames=auNamesList
		        else:
		                if "]" in aff:
		                        authorsNames, affiliation=aff.split("]")
		                        auNames=[]
		                        for sci in auNamesList:
		                                if sci[0] in authorsNames:
		                                        auNames.append(sci)
		                        affiliation=affiliation.split(',')
		                else:
		                        #in this case there is only one affiliation for all authors
		                        affiliation=aff.split(',')
		                        auNames=auNamesList
		                
		                for k in range(len(affiliation)):
		                        affiliation[k]=affiliation[k].strip()
		                        if aff.isupper():
		                                affiliation[k]=affiliation[k].capitalize()
	
	
				############### Countries ##################################################
				if "USA" in affiliation[-1] or "Ca 94043" in affiliation[-1] or "Ma 02114" in affiliation[-1]:
				        countryName="United States"
				elif "North Ireland" in affiliation[-1] or "Wales" in affiliation[-1] or "England" in affiliation[-1] or "Scotland" in affiliation[-1]:
				        countryName="United Kingdom"
				elif "China" in affiliation[-1]:
				        countryName="China"
				else:
				        countryName=affiliation[-1]
				
				try:
					current_country=Country.objects.get(name=countryName)
				except ObjectDoesNotExist:
					current_country, created=Country.objects.get_or_create(name="N.A",has_SB=True,sbw=0)
				        
				        
				current_country.has_SB=True
				current_country.save()
	
				################ Institutions #################################
				univName=affiliation[0]
				univName=cleanUnivName(univName)
				inst_query=Institution.objects.filter(name=univName)
				if inst_query.count()==1: #try to filter on the univName alone first in the case the country wasn't identified.
                                    current_inst=inst_query[0]
                                    current_country=current_inst.country
                                elif inst_query.count()>1: #If several institutions from different countries have the same name
                                    inst_query=inst_query.filter(country=current_country)
                                    if inst_query:
                                        current_inst=inst_query[0]
                                    else:
                                        current_inst=Institution(name=univName,country=current_country)
                                        current_inst.save()
                                else:
                                    current_inst=Institution(name=univName,country=current_country)
                                    current_inst.save()

                                ################ Cities ##################################################
				townName=re.search("([A-Z][a-z]+\s?)+",affiliation[-2])
				if townName:
				        townName=townName.group().strip()
				elif len(affiliation)>2:
				        townName=re.search("([A-Z][a-z]+\s?)+",affiliation[-3])
				        if townName:
				                townName=townName.group().strip()
				        else:
				                townName="N.A."
				else:
				        townName="N.A."
				            
				current_town, created=Town.objects.get_or_create(name=townName,country=current_country)
		
			########################   Scientists   ##################################################
			for au in auNames:
			        if au not in counted_au: #prevents counting the same author twice when listed under several affiliations
			                counted_au.append(au)
			                au[0]=au[0].capitalize()
			                ################### email #######################
			                email=""
			                if EM: #if an email is provided, check if it's the one of this author
			                        emails=EM.split(";")
			                        for e in emails:
			                                if au[0].lower() in e:
			                                        email=e.strip()
	
			                current_scientist, created=Person.objects.get_or_create(initials=au[1],last_name=au[0])
					current_scientist.first_name=au[1]
	
			                if not current_scientist.email and email:
			                        current_scientist.email=email
			                               
					if AF: #if the full name is provided
			        	        AFlist=AF.split("; ")
			        	        for af in AFlist:
			        	                if au[0].capitalize() in af.capitalize():
			        	                        fullName=af.split(", ")
			        	                        if len(fullName)>1:
			        	                                current_scientist.first_name=fullName[1]
			        	                        else:
			        	                                current_scientist.first_name=af.split(" ")[1]
	
					current_scientist.save()
	
			                #################### Authorship ############################
			                pos=[x[0] for x in auNamesList].index(current_scientist.last_name)+1
			                auth=Authorship(author=current_scientist,paper=new_paper,position=pos)
					auth.save()
	
					if pos==1:
						new_paper.first_au=current_scientist
						new_paper.save()
	
			                #################### Affiliations ##############################
					current_aff, created=Affiliation.objects.get_or_create(institution=current_inst,employee=current_scientist,year=PY)

		return new_paper, 1
	elif C1:
		return query[0], 0
	else:
		return "", 0




def uniquify_raw_cits():
    all_cits=Raw_cit.objects.all()
    for cit in all_cits:
        raw_cit_list=None
        if cit.doi:
            raw_cit_list=Raw_cit.objects.filter(doi=cit.doi)
            raw_cit_list=list(raw_cit_list)
            

        else: #if the cit doesn't have a doi
            raw_cit_list=Raw_cit.objects.filter(last_name=cit.last_name).filter(jour=cit.jour)
            raw_cit_list=list(raw_cit_list)
            if len(raw_cit_list)>1:
                for xcite in raw_cit_list:
                    if xcite.year and cit.year:
                        if xcite.year!=cit.year:
                            raw_cit_list.remove(xcite)
                            continue
                    if xcite.vol and cit.vol:
                        if xcite.vol!=cit.vol:
                            raw_cit_list.remove(xcite)
                            continue
                    if xcite.page and cit.page:
                        if xcite.page!=cit.page:
                            raw_cit_list.remove(xcite)
                            continue

        if len(raw_cit_list)>1:
            #identifies the raw_cit associated with the good paper 
            gpaper=None
            gcit=None
            for r in raw_cit_list:
                p=r.get_paper()
                if p.title:
                    gpaper=p
                    gcit=r
                    break

            if not gcit:
                gcit=raw_cit_list[0]
                gpaper=gcit.get_paper()

            for r in raw_cit_list:
                if r!=gcit:
                    #correct citations for duplicate cits
                    if not gcit.doi and r.doi:
                        gcit.doi=r.doi
                        gcit.save()
                        
                    p=r.get_paper()
                    if p!=gpaper:
                        wcitations=Citation.objects.filter(cited_paper=p)
                        for w in wcitations:
                            w.cited_paper=gpaper
                            w.save()

                        p.delete()
                    print r.cit
                    r.delete()  
                
            

def corr_jour():
    prog = re.compile("(?P<last_name>\w+)[.\s](?P<init>\w+)(?:,\s)?(?P<year>\d+)?(?:,\s)(?P<journal>(?:[\s-]?\w+)+)(?:,\s)?(?P<vol>V\d+)?(?:,\s)?(?P<page>[PE]\d+)?(?:,\s)?(?P<doi>DOI .+$)?",re.UNICODE)
    all_cits=Raw_cit.objects.all()
    for cit in all_cits:
        m=prog.match(cit.cit)
        last_name,init,year,journal,vol,page,doi=m.groups()
        cited_jour, created=Journal.objects.get_or_create(short_name=journal.capitalize())
        if created:
            try:
                cited_jour.get_name()
                print cited_jour.name
            except:
                print "!!!"+cited_jour.short_name
        
        
def merge_persons(pk1,pk2):
    p1=Person.objects.get(pk=pk1)
    p2=Person.objects.get(pk=pk2)
    aus2=Authorship.objects.filter(author=p2)
    for au in aus2:
        au.author=p1
        au.save()

    aff2=Affiliation.objects.filter(employee=p2)
    for aff in aff2:
        aff.employee=p1
        aff.save()

    first_au_pap=Paper.objects.filter(first_au=p2)
    for pap in first_au_pap:
        pap.first_au=p1
        pap.save()

    p2.delete()
    p1.get_SBW()
    

    
        
        
