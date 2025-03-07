import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Union, Tuple
from enum import Enum

class AttributeType(Enum):
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    STRING = "string"

@dataclass
class ParseError(Exception):
    """Custom exception for rule parsing errors"""
    message: str
    position: int
    token: str = ""

    def __str__(self):
        if self.token:
            return f"Parse error at position {self.position}: {self.message} (found '{self.token}')"
        return f"Parse error at position {self.position}: {self.message}"

@dataclass
class AttributeDefinition:
    name: str
    attr_type: AttributeType
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    allowed_values: Optional[Set[str]] = None

class AttributeCatalog:
    def __init__(self):
        self.attributes: Dict[str, AttributeDefinition] = {}
    
    def add_attribute(self, definition: AttributeDefinition) -> None:
        if definition.name in self.attributes:
            raise ValueError(f"Attribute {definition.name} already exists")
        
        # Validate attribute definition
        if definition.attr_type in [AttributeType.INTEGER, AttributeType.FLOAT]:
            if definition.min_value is not None and definition.max_value is not None:
                if definition.min_value > definition.max_value:
                    raise ValueError("Min value cannot be greater than max value")
        
        if definition.attr_type == AttributeType.STRING and not definition.allowed_values:
            raise ValueError("String attributes must have allowed values")
            
        if definition.attr_type == AttributeType.BOOLEAN:
            if definition.min_value is not None or definition.max_value is not None:
                raise ValueError("Boolean attributes cannot have min/max values")
        
        self.attributes[definition.name] = definition
    
    def validate_value(self, attr_name: str, value: Any) -> bool:
        if attr_name not in self.attributes:
            raise ValueError(f"Unknown attribute: {attr_name}")
            
        attr = self.attributes[attr_name]
        
        if attr.attr_type == AttributeType.INTEGER:
            if not isinstance(value, int):
                return False
            if attr.min_value is not None and value < attr.min_value:
                return False
            if attr.max_value is not None and value > attr.max_value:
                return False
                
        elif attr.attr_type == AttributeType.FLOAT:
            if not isinstance(value, (int, float)):
                return False
            if attr.min_value is not None and value < attr.min_value:
                return False
            if attr.max_value is not None and value > attr.max_value:
                return False
                
        elif attr.attr_type == AttributeType.BOOLEAN:
            if not isinstance(value, bool):
                return False
                
        elif attr.attr_type == AttributeType.STRING:
            if not isinstance(value, str):
                return False
            if value not in attr.allowed_values:
                return False
                
        return True

class condition:
    def __init__(self, attribute: str, operator: str, value: Any, invertion: bool = False):
        self.attribute = attribute
        self.operator = operator
        self.value = value
        self.invertion = invertion
    
    def eval(self, candidate: Dict[str, Any]) -> bool:
        if self.attribute not in candidate:
            raise ValueError(f"Missing attribute: {self.attribute}")
            
        result = False
        if self.operator == "=":
            result = candidate[self.attribute].lower() == self.value.lower() if isinstance(self.value, str) else candidate[self.attribute] == self.value
        elif self.operator == "<":
            result = candidate[self.attribute] < self.value
        elif self.operator == ">":
            result = candidate[self.attribute] > self.value
        elif self.operator == "<=":
            result = candidate[self.attribute] <= self.value
        elif self.operator == ">=":
            result = candidate[self.attribute] >= self.value
            
        return not result if self.invertion else result

class operation:
    def __init__(self, operator: str, invertion: bool = False):
        self.operator = operator
        self.children = set()
        self.invertion = invertion
    
    def add(self, child: Union['operation', condition]) -> None:
        self.children.add(child)
    
    def eval(self, candidate: Dict[str, Any]) -> bool:
        if not self.children:
            return True
            
        results = [child.eval(candidate) for child in self.children]
        
        if self.operator == "and":
            result = all(results)
        else:  # or
            result = any(results)
            
        return not result if self.invertion else result

class decision:
    def __init__(self, attribute: str, operator: str, value: Any, true_tree: Any = None, false_tree: Any = None):
        self.attribute = attribute
        self.operator = operator
        self.value = value
        self.true_tree = true_tree
        self.false_tree = false_tree
        
    def eval(self, candidate: Dict[str, Any]) -> Any:
        if self.attribute not in candidate:
            raise ValueError(f"Missing attribute: {self.attribute}")
            
        if self.operator == "=":
            result = candidate[self.attribute].lower() == self.value.lower() if isinstance(self.value, str) else candidate[self.attribute] == self.value
            return self.true_tree if result else self.false_tree
        elif self.operator == "<":
            return self.true_tree if candidate[self.attribute] < self.value else self.false_tree
        elif self.operator == ">":
            return self.true_tree if candidate[self.attribute] > self.value else self.false_tree
        elif self.operator == "<=":
            return self.true_tree if candidate[self.attribute] <= self.value else self.false_tree
        elif self.operator == ">=":
            return self.true_tree if candidate[self.attribute] >= self.value else self.false_tree

class result_node:
    def __init__(self, value: Any):
        self.value = value
        
    def eval(self, candidate: Dict[str, Any]) -> Any:
        return self.value

class Rule:
    def __init__(self, name: str, rule_str: str, ast: Union[condition, operation], decision_tree: Optional[decision] = None):
        self.name = name
        self.rule_str = rule_str
        self.ast = ast
        self.decision_tree = decision_tree

class RuleParser:
    VALID_OPERATORS = {'=', '<', '>', '<=', '>='}
    VALID_LOGICAL_OPERATORS = {'AND', 'OR', 'NOT'}
    
    @staticmethod
    def validate_tokens(tokens: List[str]) -> None:
        """Validate basic token structure and presence"""
        if not tokens:
            raise ParseError("Empty rule string", 0)
        
        # Check for unmatched parentheses
        paren_count = 0
        for pos, token in enumerate(tokens):
            if token == '(':
                paren_count += 1
            elif token == ')':
                paren_count -= 1
            if paren_count < 0:
                raise ParseError("Unmatched closing parenthesis", pos, token)
        if paren_count > 0:
            raise ParseError("Unmatched opening parenthesis", len(tokens) - 1)

    @staticmethod
    def tokenize_rule(rule: str) -> List[str]:
        """Enhanced tokenizer with basic validation"""
        if not isinstance(rule, str):
            raise TypeError("Rule must be a string")
        
        if not rule.strip():
            raise ParseError("Empty rule string", 0)
        
        # Add spaces around operators and parentheses
        rule = re.sub(r'([()])', r' \1 ', rule)
        rule = re.sub(r'(<=|>=|=|<|>)', r' \1 ', rule)
        
        # Split and filter out empty tokens
        tokens = [t for t in rule.split() if t.strip()]
        
        # Basic validation of token structure
        RuleParser.validate_tokens(tokens)
        
        return tokens

    @staticmethod
    def parse_condition(tokens: List[str], pos: int) -> Tuple[condition, int]:
        """Parse a condition with error handling"""
        if pos >= len(tokens):
            raise ParseError("Unexpected end of rule while parsing condition", pos)
        
        # Handle NOT operator
        invertion = False
        if tokens[pos] == 'NOT':
            invertion = True
            pos += 1
            if pos >= len(tokens):
                raise ParseError("Unexpected end of rule after NOT operator", pos)
        
        # Parse attribute
        if pos >= len(tokens):
            raise ParseError("Missing attribute in condition", pos)
        attribute = tokens[pos]
        if attribute in RuleParser.VALID_OPERATORS or attribute in RuleParser.VALID_LOGICAL_OPERATORS:
            raise ParseError("Invalid attribute name", pos, attribute)
        
        # Parse operator
        pos += 1
        if pos >= len(tokens):
            raise ParseError(f"Missing operator after attribute '{attribute}'", pos)
        operator = tokens[pos]
        if operator not in RuleParser.VALID_OPERATORS:
            raise ParseError("Invalid comparison operator", pos, operator)
        
        # Parse value
        pos += 1
        if pos >= len(tokens):
            raise ParseError(f"Missing value after operator '{operator}'", pos)
        value = tokens[pos].strip("'")
        
        # Attempt to convert value to appropriate type
        try:
            if value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False
            else:
                try:
                    value = int(value)
                except ValueError:
                    try:
                        value = float(value)
                    except ValueError:
                        pass  # Keep as string if not numeric
        except Exception as e:
            raise ParseError(f"Invalid value format: {str(e)}", pos, value)
            
        return condition(attribute, operator, value, invertion), pos + 1

    @staticmethod
    def parse_expression(tokens: List[str], start: int = 0) -> Tuple[Union[condition, operation], int]:
        """Parse an expression with error handling"""
        if start >= len(tokens):
            raise ParseError("Unexpected end of rule", start)
        
        current_operation = None
        pos = start
        
        while pos < len(tokens):
            token = tokens[pos]
            
            if token == '(':
                sub_expr, new_pos = RuleParser.parse_expression(tokens, pos + 1)
                if new_pos >= len(tokens) or tokens[new_pos] != ')':
                    raise ParseError("Missing closing parenthesis", new_pos)
                
                if current_operation:
                    current_operation.add(sub_expr)
                else:
                    return sub_expr, new_pos + 1
                pos = new_pos + 1
                
            elif token == ')':
                if not current_operation:
                    raise ParseError("Unexpected closing parenthesis", pos)
                return current_operation, pos
                
            elif token in ('AND', 'OR'):
                if not current_operation:
                    current_operation = operation(token.lower())
                elif current_operation.operator != token.lower():
                    # Wrap current operation in new one if operators don't match
                    new_op = operation(token.lower())
                    new_op.add(current_operation)
                    current_operation = new_op
                pos += 1
                
            elif token == 'NOT':
                cond, new_pos = RuleParser.parse_condition(tokens, pos)
                if current_operation:
                    current_operation.add(cond)
                else:
                    return cond, new_pos
                pos = new_pos
                
            else:
                cond, new_pos = RuleParser.parse_condition(tokens, pos)
                if current_operation:
                    current_operation.add(cond)
                else:
                    return cond, new_pos
                pos = new_pos
                
            if pos >= len(tokens) and current_operation:
                return current_operation, pos
                
        raise ParseError("Unexpected end of rule", pos)

def parse_rule(rule_str: str) -> Union[condition, operation]:
    """Main entry point for rule parsing with error handling"""
    try:
        tokens = RuleParser.tokenize_rule(rule_str)
        ast, pos = RuleParser.parse_expression(tokens)
        
        # Check if there are any unused tokens
        if pos < len(tokens):
            raise ParseError("Unexpected tokens after valid expression", pos, tokens[pos])
        
        return ast
    except ParseError:
        raise
    except Exception as e:
        raise ParseError(f"Unexpected error while parsing rule: {str(e)}", 0)

def transform_to_decision_tree(ast):
    def find_conditions(node):
        conditions = set()
        if isinstance(node, condition):
            conditions.add((node.attribute, node.operator, node.value))
        elif isinstance(node, operation):
            for child in node.children:
                conditions.update(find_conditions(child))
        return conditions
    
    def create_decision_tree(node, remaining_conditions):
        if not remaining_conditions:
            if isinstance(node, bool):
                return result_node(node)
            return result_node(node.eval({}))
        
        attr, op, val = remaining_conditions.pop()
        new_conditions = remaining_conditions.copy()
        
        cond = condition(attr, op, val)
        
        true_candidate = {attr: val}
        false_candidate = {attr: val - 1 if isinstance(val, (int, float)) else val}
        
        if isinstance(node, operation):
            true_result = node.eval(true_candidate)
            false_result = node.eval(false_candidate)
        else:
            true_result = node.eval(true_candidate)
            false_result = node.eval(false_candidate)
        
        decision_node = decision(attr, op, val)
        
        decision_node.true_tree = create_decision_tree(true_result, new_conditions.copy())
        decision_node.false_tree = create_decision_tree(false_result, new_conditions.copy())
        
        return decision_node
    
    conditions = find_conditions(ast)
    return create_decision_tree(ast, conditions)

class RuleEngine:
    def __init__(self, catalog: AttributeCatalog):
        self.catalog = catalog
        self.rules: Dict[str, Rule] = {}
    
    def create_rule(self, name: str, rule_str: str) -> Rule:
        if name in self.rules:
            raise ValueError(f"Rule {name} already exists")
        
        # Parse rule into AST
        ast = parse_rule(rule_str)
        
        # Validate attributes in the rule against catalog
        def validate_attributes(node):
            if isinstance(node, condition):
                if node.attribute not in self.catalog.attributes:
                    raise ValueError(f"Unknown attribute in rule: {node.attribute}")
            elif isinstance(node, operation):
                for child in node.children:
                    validate_attributes(child)
        
        validate_attributes(ast)
        
        # Transform AST to decision tree
        decision_tree = transform_to_decision_tree(ast)
        
        # Create and store rule
        rule = Rule(name, rule_str, ast, decision_tree)
        self.rules[name] = rule
        return rule
    
    def modify_rule(self, name: str, new_rule_str: str) -> Rule:
        if name not in self.rules:
            raise ValueError(f"Rule {name} does not exist")
        
        self.rules.pop(name)
        return self.create_rule(name, new_rule_str)
    
    def combine_rules(self, name: str, rule_names: List[str], operator: str) -> Rule:
        if operator.lower() not in ['and', 'or']:
            raise ValueError("Operator must be 'and' or 'or'")
            
        if name in self.rules:
            raise ValueError(f"Rule {name} already exists")
        
        # Create new operation node
        combined_operation = operation(operator.lower())
        
        # Add each rule's AST as a child
        for rule_name in rule_names:
            if rule_name not in self.rules:
                raise ValueError(f"Rule {rule_name} does not exist")
            combined_operation.add(self.rules[rule_name].ast)
        
        # Create decision tree from combined AST
        decision_tree = transform_to_decision_tree(combined_operation)
        
        # Create rule string
        rule_str = f" {operator} ".join(f"({self.rules[name].rule_str})" for name in rule_names)
        
        # Create and store new rule
        rule = Rule(name, rule_str, combined_operation, decision_tree)
        self.rules[name] = rule
        return rule
    
    def evaluate(self, rule_name: str, candidate: Dict[str, Any]) -> bool:
        if rule_name not in self.rules:
            raise ValueError(f"Rule {rule_name} does not exist")
        
        # Validate candidate data against catalog
        for attr_name, value in candidate.items():
            if attr_name in self.catalog.attributes:
                if not self.catalog.validate_value(attr_name, value):
                    raise ValueError(f"Invalid value for attribute {attr_name}: {value}")
        
        # Evaluate using decision tree
        current_node = self.rules[rule_name].decision_tree
        while not isinstance(current_node, result_node):
            current_node = current_node.eval(candidate)
        return current_node.value