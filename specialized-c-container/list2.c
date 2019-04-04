#include "NuitkaAPI.c"

int list_sum()
{
	int a = 7;
	NuitkaList *result = newList(1);
	NuitkaList_SetItem(result,0,a);
	int i = 0;
	for(;i<7;i++)
	{
		NuitkaList_Append(result,a);
	}
	return NuitkaList_Sum(result);
	
}
