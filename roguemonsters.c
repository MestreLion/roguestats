// roguemonsters: Generate random monsters using Rogue rules
//
//    Copyright (C) 2015 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
//    portions  (C) 1981 Michael Toy, Ken Arnold, and Glenn Wichman
//    portions  (C) 1983 Mel Sibony, Jon Lane (AI Design update for the IBMPC)
//
// Using the algorithms from Rogue, generates random level and wander monsters.
// Pseudo-random functions and monster rules for each level are taken from
// Rogue source code, PC-DOS version 1.1 published by A.I. Design itself.
// Algorithms are the same in v1.48 published by Enyx.
// Relevant code was gathered mostly from MONSTERS.C and MAIN.C

#include <stdio.h>
#include <string.h>
#include <time.h>

#define PROGNAME "roguemonsters"
#define MONSTERS 100
#define LEVELS   30

#define TRUE	1
#define FALSE	0
#define is_bool(x) (x == TRUE || x == FALSE)
typedef unsigned char bool;


////////////////////////////////////////////
// ROGUE code (adaptations marked with //@)

long seed; /* Random number seed */

/*
 * Random number generator -
 * adapted from the FORTRAN version
 * in "Software Manual for the Elementary Functions"
 * by W.J. Cody, Jr and William Waite.
 */
long ran()
{
	seed *= 125;
	seed -= (seed / 2796203) * 2796203;
	return seed;
}

/*
 * rnd:
 *	Pick a very random number.
 */
int rnd(int range)
{
	return range < 1 ? 0 : ((ran() + ran()) & 0x7fffffffl) % range;
}

/*
 * returns a seed for a random number generator
 */
long srand()
{
	/*
	 * Get Time
	 */
	//@ bdos(0x2C);
	//@ return(regs->cx + regs->dx);

	//@ time(NULL) as seed is roughly equivalent as DOS interrupt 0x2C
	//@ except for the lack of millisecond accuracy. But it's portable :)
	return (long) time(NULL);
}

/*
 * List of monsters in rough order of vorpalness
 */
static char *lvl_mons  = "K BHISOR LCA NYTWFP GMXVJD";
static char *wand_mons = "KEBHISORZ CAQ YTW PUGM VJ ";

/*
 * randmonster:
 *	Pick a monster to show up.  The lower the level,
 *	the meaner the monster.
 */
char randmonster(int level, bool wander)
{
	int d;
	char *mons;

	mons = wander ? wand_mons : lvl_mons;
	do {
		int r10 = rnd(5) + rnd(6);
		d = level + (r10 - 5);
		if (d <  1) d = rnd(5) + 1;
		if (d > 26) d = rnd(5) + 22;
	} while (mons[--d] == ' ');
	return mons[d];
}

// END of Rogue code
////////////////////////////////////////////////


void usage()
{
	printf("Usage: %s [MONSTERS] [LEVELS]\n", PROGNAME);
	printf("\tGenerates <MONSTERS> [default: %d] monsters for", MONSTERS);
	printf(" each one of <LEVELS> [default: %d] levels,\n", LEVELS);
	printf("\tprinting a line of generated level monsters and a line of wander monsters\n");
	printf("\tchosen randomly according to Rogue level rules\n");
}


bool readint(char* str, int* value, char* valuename) {
	int res = sscanf(str, "%d", value);  // "%hhu" for bool parse
	if (!res || *value <= 0) {
		printf("Invalid number of %s: %s\n", valuename, str);
		usage();
		return FALSE;
	}
	return TRUE;
}


int main(int argc, char *argv[])
{
	seed = srand();

	int levels = LEVELS;
	int monsters = MONSTERS;
	int i, level;
	bool wander;

	for (i=1; i < argc; i++) {
		if (strcmp(argv[i], "-h") == 0 || strcmp(argv[i], "--help") == 0) {
			usage();
			return 0;
		}
	}
	if (argc > 3) {
		usage();
		return 1;
	}

	if (argc >= 2 && !readint(argv[1], &monsters, "MONSTERS")) return 1;
	if (argc >= 3 && !readint(argv[2], &levels,   "LEVELS"))   return 1;

	for (level = 1; level <= levels; level++) {
		for (wander = FALSE; is_bool(wander); wander++) {
			for (i = 0; i < monsters; i++) {
				printf("%c", randmonster(level, wander));
			}
			printf("\n");
		}
	}

	return 0;
}
