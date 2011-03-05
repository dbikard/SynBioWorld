from .models import Paper, Person, Journal, Institution, Country, Town, Citation, Authorship, Affiliation
from django.core.exceptions import ObjectDoesNotExist

import re

def update_SBW():
	 classes=[Paper, Person, Journal, Institution, Country]
	 for c in classes:
		 entities=c.objects.all()
		 for e in entities:
			 e.get_SBW()
			 print e, e.sbw

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

def get_cited_paper(cit):
	
	cit_data=cit.split(", ")
	
	if "DOI" in cit_data[-1]:
		cited_DOI=cit_data[-1].split(' ')[1].strip()
		cited_paper=Paper.objects.filter(doi=cited_DOI)
	
	elif len(cit_data)==1:
		cit_title=cit_data[0].capitalize()
		cited_paper=Paper.objects.filter(title=cit_title)
	
	elif len(cit_data)>2:
		cited_first_au=cit_data[0].split(' ')
		cited_last_name, cited_init = ' '.join(cited_first_au[:-1]), cited_first_au[-1].strip()
		cited_last_name=cited_last_name.strip().capitalize()
		try:
			cited_year=int(cit_data[1])
			cited_jour=cit_data[2].capitalize()
		except:
			return None
		
		try:
			cited_first_au=Person.objects.get(last_name=cited_last_name, initials=cited_init)
		except ObjectDoesNotExist:
			cited_first_au=None
		
		
		if cited_first_au:
			cited_paper=Paper.objects.filter(first_au=cited_first_au).filter(pubYear=cited_year)
	
			cited_jour=Journal.objects.filter(short_name=cited_jour)
			cited_jour=list(cited_jour)
			if cited_jour:
				cited_jour=cited_jour[0]
				cited_paper=cited_paper.filter(journal=cited_jour)
	
			if len(cit_data)>3:
				vol=cit_data[3][1:]
				cited_paper=cited_paper.filter(volume=vol)
	
		else:
			cited_paper=[]
	else: #case not considered
		cited_paper=[]
	
	if type(cited_paper)!=Paper:
		cited_paper=list(cited_paper)
		if len(cited_paper)==1:
			cited_paper=cited_paper[0]
			return cited_paper
	else:
		return cited_paper




def parse_ISI_data(data):
	months={"jan":1,"feb":2,"mar":3,"apr":4,"may":5,"jun":6,"jul":7,"aug":8,"sep":9,"oct":10,"nov":11,"dec":12}


	PT,AU,BA,ED,GP,AF,CA,TI,SO,SE,LA,DT,CT,CY,CL,SP,HO,DE,ID,AB,C1,RP,EM,FU,FX,CR,NR,TC,PU,PI,PA,SN,BN,DI,J9,JI,PD,PY,VL,IS,PN,SU,SI,BP,EP,AR,DI2,PG,SC,GA,UT = data
	TI=TI.capitalize()
	
	query=Paper.objects.filter(title=TI) #Tests if the paper is already in the database
	if C1 and not query:
		auNamesList=[[j.strip() for j in i.split(", ")] for i in AU.split(";")]
	
		############# Journal #############
		SO=SO.capitalize()
		jour, created=Journal.objects.get_or_create(name=SO)
	
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
		new_paper=Paper(title = TI,
				journal = jour,
				volume = VL,
				pubMonth = int(PM),
				pubYear = int(PY),
				abstract=AB,
				doi=DI,
				raw_citations=CR,
				)
		new_paper.save()
	
	
		############## Authors - Affiliations ####################
		counted_au=[] #used not to count authors twice when they have several affiliations for a same paper
		corres_au=RP.split(",")[0]
		if "[" in C1:
		        affs=C1[1:].split("; [")
		elif  ";" in C1: #in this case, there are several affiliations bu we don't who belongs to what institution.
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
		                current_countryID=None
		                current_key=None
		                inst=None
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
	
				################ Institutions #################################
				univName=affiliation[0]
				univName=cleanUnivName(univName)
				inst, created=Institution.objects.get_or_create(name=univName,country=current_country)
		
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
					if inst:
			                	current_aff, created=Affiliation.objects.get_or_create(institution=inst,employee=current_scientist,year=PY)

		return new_paper, 1
	elif C1:
		return query[0], 0
	else:
		return "", 0
