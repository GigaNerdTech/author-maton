#include <cstring>
#include <cstdlib>
#include <cstdio>

#include "mythes.hxx"

extern char * mystrdup(const char * s);

using namespace std;

int 
main(int argc, char** argv)
{

    char * af;
    char * df;
    char * wtc;
    FILE* wtclst;

  /* first parse the command line options */
  /* arg1 - index file, arg2 thesaurus data file, arg3 - file of words to check */

  if (argv[1]) {
       af = mystrdup(argv[1]);
  } else {
    fprintf(stderr,"correct syntax is:\n"); 
    fprintf(stderr,"example index_file thesaurus_file file_of_words_to_check\n");
    exit(1);
  }
  if (argv[2]) {
       df = mystrdup(argv[2]);
  } else {
    fprintf(stderr,"correct syntax is:\n"); 
    fprintf(stderr,"example index_file thesaurus_file file_of_words_to_check\n");
    exit(1);
  }
  if (argv[3]) {
       wtc = mystrdup(argv[3]);
  } else {
    fprintf(stderr,"correct syntax is:\n"); 
    fprintf(stderr,"example index_file thesaurus_file file_of_words_to_check\n");
    exit(1);
  }

  
  /* open the words to check list */
//  wtclst = fopen(wtc,"r");
//  if (!wtclst) {
//    fprintf(stderr,"Error - could not open file of words to check\n");
//    exit(1);
//  }

    // open a new thesaurus object
    MyThes * pMT= new MyThes(af,df);

    // get the encoding used for the thesaurus data
    char * encoding = pMT->get_th_encoding();
//    fprintf(stdout,"Thesaurus uses encoding %s\n\n",encoding);
    
    int k;
    char buf[101];
    mentry * pmean;
	strcpy(buf,wtc);
//    while(fgets(buf,100,wtclst)) {
      k = strlen(buf);
      *(buf + k) = '\0';
      int len = strlen(buf);
      int count = pMT->Lookup(buf,len,&pmean);
      // don't change value of pmean
      // or count since needed for CleanUpAfterLookup routine
      mentry* pm = pmean;
      if (count) {
//        fprintf(stdout,"%s has %d meanings\n",buf,count);
	for (int  i=0; i < count; i++) {
          fprintf(stdout,"   meaning %d: %s\n",i,pm->defn);
          for (int j=0; j < pm->count; j++) {
	    fprintf(stdout,"       %s\n",pm->psyns[j]);
          }
          fprintf(stdout,"\n");
          pm++;
	}
        fprintf(stdout,"\n\n");
        // now clean up all allocated memory 
        pMT->CleanUpAfterLookup(&pmean,count);
      } else {
        fprintf(stdout,"\"%s\" is not in thesaurus!\n",buf);
      }

    delete pMT;
    free(wtc);
    free(df);
    free(af);

    return 0;
}

