#include <stdio.h>
#include <stdlib.h>
int main(int argc, char *argv[])
{
  int *array;
  int size;
  int i;
  int sum = 0;
  printf("enter the array size\n");
  scanf("%d", &size);

  array = malloc(size * sizeof(int));
  for(i=0; i < size; i++){
    	scanf("%d",&array[i]);
    	sum+=array[i];
  	}
  printf("If you want to enter more type 1:- ");
  int more;
  scanf("%d",&more);
  while (more == 1){
  	more = 0;
  	int *newarray;
  	newarray = malloc(size * sizeof(int));
  	for(i=0; i < size; i++){
    	scanf("%d",&newarray[i]);
    	sum+=newarray[i];
  	}
	printf("If you want to enter more type 1:- ");
  	scanf("%d",&more);
  	free(newarray);
}

  free(array);
  printf("%d\n", sum);
  return 0;
}