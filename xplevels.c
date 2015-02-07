#include <stdio.h>
#include <stdlib.h>

long *e_levels;		/* Pointer to array of experience level */


/*
 * init_ds()
 *   Allocate things data space
 */
void //@
init_ds(clrflag)
	int clrflag;
{
	register long *ep;
	//@ e_levels = (long *)newmem(20 * sizeof (long));
	e_levels = (long *)malloc(20 * sizeof (long));
	for (ep = e_levels+1, *e_levels = 10L; ep < e_levels + 19; ep++)
		*ep = *(ep-1) << 1;
	*ep = 0L;
}


/*
 * check_level:
 *	Check to see if the guy has gone up a level.
 */
void //@
check_level()
{
/*@
    register int i, add, olevel;

    for (i = 0; e_levels[i] != 0; i++)
	if (e_levels[i] > pstats.s_exp)
	    break;
    i++;
    olevel = pstats.s_lvl;
    pstats.s_lvl = i;
    if (i > olevel)
    {
	add = roll(i - olevel, 10);
	max_hp += add;
	if ((pstats.s_hpt += add) > max_hp)
	    pstats.s_hpt = max_hp;
	    msg("and achieve the rank of \"%s\"", he_man[i-1]);
    }
*/
}


int main(int argc, char *argv[])
{
	int i;

	init_ds();
	for (i = 0; e_levels[i] != 0; i++)
		printf("XP level %2d: %10ld\n", i+2, e_levels[i]);

	free(e_levels);  //@
	return 0;
}
