int globalBuffer[100];

typedef struct
{
	//iter points after the last element
	int iter;

}NuitkaList;

NuitkaList *newList(int n)
{
	NuitkaList l;
	NuitkaList *list = &l;
	list->iter = n;
	return list;
}

int NuitkaList_SetItem(NuitkaList *list,int i,int item)
{
	//if overflow return 1
	if(list->iter>=i){
		return 1;
	}
	globalBuffer[i] = item;
	//if successful return 0
	return 0;

}

int NuitkaList_Append(NuitkaList *list,int item)
{
	//if overflow return 1
	if(item>=100)return 1;

	//append the new value at the end of the list
	//and increase iter by one
	globalBuffer[list->iter] = item;
	list->iter = list->iter + 1;
	//if successful return 0
	return 0;
}
int NuitkaList_Sum(NuitkaList *list)
{
	int sum = 0;
	int i = 0;
	for(; i <list->iter;i++)
	{
		sum = sum + globalBuffer[i];
	}
	return sum;

}
