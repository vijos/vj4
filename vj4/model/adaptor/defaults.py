DEFAULT_CODE_TEMPLATES = {
    'c': r"""
#include <stdio.h>

int main()
{
    printf("hello, world\n");
    return 0;
}
""",
    'cc': r"""
#include <iostream>

using namespace std;

int main()
{
    cout << "hello, world" << endl;
    return 0;
}
""",
    'pas': r"""
begin
    writeln('hello, world');
end.
""",
    'java': r"""
import java.io.*;
import java.util.Scanner;

public class Main {

    /**
     * @param args
     * @throws IOException 
     */
    public static void main(String[] args) throws IOException {
        Scanner sc = new Scanner(System.in);
        System.out.println("hello, world");
    }
}
""",
    'py': r"""
print 'hello, world'
"""}
