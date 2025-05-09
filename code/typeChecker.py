import sys
from enum import Enum

import parser

class IDType(Enum):
    FUNCTION = 1
    INT = 2

class FunType:
    def __init__(self, paramCount):
        self.paramCount = paramCount
    
    def __ne__(self, value):
        #print(self, value)
        result = self.paramCount != value.paramCount
        #print(result)
        return result
    
    def __str__(self):
        return "FunType(int {self.paramCount})".format(self=self)
    
    def __repr__(self):
        return self.__str__()

class IdentifierAttributes:
    pass

class FunAttributes(IdentifierAttributes):
    def __init__(self, defined, global_):
        self.defined = defined
        self.global_ = global_

 
class StaticAttributes(IdentifierAttributes):
    def __init__(self, initialVal, global_):
        self.initialVal = initialVal
        self.global_ = global_

class LocalAttributes(IdentifierAttributes):
    pass

class InitialValue:
    pass

class Tentative(InitialValue):
    pass

class Initial(InitialValue):
    def __init__(self, value):
        self.value = value

class NoInitializer(InitialValue):
    pass

def typeCheckExpression(exp, symbolTable):
    match exp:
        case parser.FunctionCall_Exp(identifier=id, argumentList = argumentList):
            
            if symbolTable[id][0] == IDType.INT:
                print("Error: Variable {0} used as function name.".format(id))
                sys.exit(1)

            #es una funcion, parametrizaje
            paramCount = 0
            if argumentList:
                paramCount = len(argumentList)

            if symbolTable[id][1].paramCount != paramCount:
                #print(paramCount)
                print("Error: Function {0}() called with the wrong number of arguments.".format(id))
                sys.exit(1)
            
            if argumentList:
                for exp in argumentList:
                    typeCheckExpression(exp, symbolTable)
                    

        case parser.Var_Expression(identifier=id):
            if symbolTable[id][0] != IDType.INT:
                #symbolTable[id][1]
                print("ERROR: Function {0}() used as variable.".format(id))
                sys.exit(1)
        
        case parser.Assignment_Expression(lvalue=lvalue, exp=exp):
            typeCheckExpression(lvalue, symbolTable)
            typeCheckExpression(exp, symbolTable)

        case parser.Constant_Expression(intValue=intValue):
            pass 

        case parser.Unary_Expression(operator=op, expression=exp):
            typeCheckExpression(exp, symbolTable)
                          

        case parser.Binary_Expression(operator=op, left=left, right=right):
            typeCheckExpression(left, symbolTable)
            typeCheckExpression(right, symbolTable)


        case parser.Conditional_Expression(condExp=condExp, thenExp=thenExp, elseExp=elseExp):
            typeCheckExpression(condExp, symbolTable)
            typeCheckExpression(thenExp, symbolTable)
            typeCheckExpression(elseExp, symbolTable)

        case _:
            print(type(exp))
            print("Invalid expression type.")
            sys.exit(1)

def typeCheckVarDeclaration(VarDecl, symbolTable):
    symbolTable[VarDecl.identifier] = (IDType.INT,)
    if VarDecl.exp:
        typeCheckExpression(VarDecl.exp, symbolTable)
        #print(type(VarDecl.exp))
        

def typeCheckDeclaration(dec, symbolTable):
    match dec:
        case parser.VarDecl(variableDecl = variableDecl):
            typeCheckVarDeclaration(variableDecl, symbolTable)
            
        case parser.FunDecl(funDecl = funDecl):
            typeCheckFunctionDeclaration(funDecl, symbolTable)

def typeCheckForInit(forInit, symbolTable):
    match forInit:
        case parser.InitDecl(varDecl = varDecl):
            typeCheckVarDeclaration(varDecl, symbolTable)
        
        case parser.InitExp(exp=exp):
            if exp:
                typeCheckExpression(exp, symbolTable)

def typeCheckStatement(statement, symbolTable):
    match statement:
        case parser.BreakStatement():
            pass

        case parser.ContinueStatement():
            pass

        case parser.ForStatement(forInit=forInit, condExp=condExp, postExp=postExp, statement=statement, identifier=identifier):
            typeCheckForInit(forInit, symbolTable)
            
            if condExp:
                typeCheckExpression(condExp, symbolTable)

            if postExp:
                typeCheckExpression(postExp, symbolTable)

            typeCheckStatement(statement, symbolTable)
        
        case parser.DoWhileStatement(statement=statement, condExp=condExp, identifier=id):
            typeCheckStatement(statement, symbolTable)
            typeCheckExpression(condExp, symbolTable)

        case parser.WhileStatement(condExp=condExp, statement=statement, identifier=id):
            typeCheckExpression(condExp, symbolTable)
            typeCheckStatement(statement, symbolTable)

        case parser.ExpressionStmt(exp=exp):
            typeCheckExpression(exp, symbolTable)
            

        case parser.ReturnStmt(expression=exp):
            typeCheckExpression(exp, symbolTable)
            
        case parser.IfStatement(exp=exp, thenS=thenS, elseS=elseS):
            typeCheckExpression(exp, symbolTable)
            typeCheckStatement(thenS, symbolTable)

            if elseS:
                typeCheckStatement(elseS, symbolTable)

            
        case parser.CompoundStatement(block=block):
            typeCheckBlock(block, symbolTable)

        case parser.NullStatement():
            pass


def typeCheckBlock(block, symbolTable):
    if block.blockItemList:
        for i in block.blockItemList:
            match i:
                case parser.D(declaration=dec):
                    typeCheckDeclaration(dec, symbolTable)
                    
                case parser.S(statement=statement):
                    typeCheckStatement(statement, symbolTable)
                    
        
def typeCheckFunctionDeclaration(funDec, symbolTable):
    funType = FunType(len(funDec.paramList))
    hasBody = funDec.block != None

    #print(hasBody)

    alreadyDefined = False

    global_ = True
    
    if funDec.storageClass[1] and funDec.storageClass[1] == parser.StorageType.STATIC:
        global_ = False
    

    if funDec.iden in symbolTable:
        oldDecl = symbolTable[funDec.iden]
        #print(funDec.iden, oldDecl[0])
        #tu ya checaste que no es una variable!
        #aqui si son funciones

        if oldDecl[0] != IDType.FUNCTION:
            print("Error: OldType was not a function.")
            sys.exit(1)

        if oldDecl[1] != funType:
            print("Error: Incompatible function declarations.")
            sys.exit(1)

        alreadyDefined = oldDecl[2].defined

        if alreadyDefined and hasBody:
            print("Error: function is defined more than once.")
            sys.exit(1)

        if oldDecl[2].global_ and funDec.storageClass[1] == parser.StorageType.STATIC:
            print("Static function declaration follows non-static.")
            sys.exit(1)

        print("Global: ", global_)
        print("Old Global: ", oldDecl[2].global_)

        global_ = oldDecl[2].global_

    fattr = FunAttributes(defined=(alreadyDefined or hasBody), global_=global_)

    symbolTable[funDec.iden] = (IDType.FUNCTION, funType, fattr)

    if hasBody:
        for param in funDec.paramList:
            #print(type(param))
            symbolTable[param] = (IDType.INT, )
        
        typeCheckBlock(funDec.block, symbolTable)
    

def typeCheckProgram(pro):
    symbolTable = {}
    if pro.declList:
        for decl in pro.declList:
            typeCheckDeclaration(decl, symbolTable)

    return pro, symbolTable
