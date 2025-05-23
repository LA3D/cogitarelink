# Tool loop


<!-- WARNING: THIS FILE WAS AUTOGENERATED! DO NOT EDIT! -->

``` python
import os
# os.environ['ANTHROPIC_LOG'] = 'debug'
```

``` python
model = models[-1]
```

Anthropic provides an [interesting
example](https://github.com/anthropics/anthropic-cookbook/blob/main/tool_use/customer_service_agent.ipynb)
of using tools to mock up a hypothetical ordering system. We’re going to
take it a step further, and show how we can dramatically simplify the
process, whilst completing more complex tasks.

We’ll start by defining the same mock customer/order data as in
Anthropic’s example, plus create a entity relationship between customers
and orders:

``` python
orders = {
    "O1": dict(id="O1", product="Widget A", quantity=2, price=19.99, status="Shipped"),
    "O2": dict(id="O2", product="Gadget B", quantity=1, price=49.99, status="Processing"),
    "O3": dict(id="O3", product="Gadget B", quantity=2, price=49.99, status="Shipped")}

customers = {
    "C1": dict(name="John Doe", email="john@example.com", phone="123-456-7890",
               orders=[orders['O1'], orders['O2']]),
    "C2": dict(name="Jane Smith", email="jane@example.com", phone="987-654-3210",
               orders=[orders['O3']])
}
```

We can now define the same functions from the original example – but
note that we don’t need to manually create the large JSON schema, since
Claudette handles all that for us automatically from the functions
directly. We’ll add some extra functionality to update order details
when cancelling too.

``` python
def get_customer_info(
    customer_id:str # ID of the customer
): # Customer's name, email, phone number, and list of orders
    "Retrieves a customer's information and their orders based on the customer ID"
    print(f'- Retrieving customer {customer_id}')
    return customers.get(customer_id, "Customer not found")

def get_order_details(
    order_id:str # ID of the order
): # Order's ID, product name, quantity, price, and order status
    "Retrieves the details of a specific order based on the order ID"
    print(f'- Retrieving order {order_id}')
    return orders.get(order_id, "Order not found")

def cancel_order(
    order_id:str # ID of the order to cancel
)->bool: # True if the cancellation is successful
    "Cancels an order based on the provided order ID"
    print(f'- Cancelling order {order_id}')
    if order_id not in orders: return False
    orders[order_id]['status'] = 'Cancelled'
    return True
```

We’re now ready to start our chat.

``` python
tools = [get_customer_info, get_order_details, cancel_order]
chat = Chat(model, tools=tools)
```

We’ll start with the same request as Anthropic showed:

``` python
r = chat('Can you tell me the email address for customer C1?')
print(r.stop_reason)
r.content
```

    - Retrieving customer C1
    tool_use

    [ToolUseBlock(id='toolu_0168sUZoEUpjzk5Y8WN3q9XL', input={'customer_id': 'C1'}, name='get_customer_info', type='tool_use')]

Claude asks us to use a tool. Claudette handles that automatically by
just calling it again:

``` python
r = chat()
contents(r)
```

    'The email address for customer C1 is john@example.com.'

Let’s consider a more complex case than in the original example – what
happens if a customer wants to cancel all of their orders?

``` python
chat = Chat(model, tools=tools)
r = chat('Please cancel all orders for customer C1 for me.')
print(r.stop_reason)
r.content
```

    - Retrieving customer C1
    tool_use

    [TextBlock(text="Okay, let's cancel all orders for customer C1:", type='text'),
     ToolUseBlock(id='toolu_01ADr1rEp7NLZ2iKWfLp7vz7', input={'customer_id': 'C1'}, name='get_customer_info', type='tool_use')]

This is the start of a multi-stage tool use process. Doing it manually
step by step is inconvenient, so let’s write a function to handle this
for us:

------------------------------------------------------------------------

<a
href="https://github.com/AnswerDotAI/claudette/blob/main/claudette/toolloop.py#L16"
target="_blank" style="float:right; font-size:smaller">source</a>

### Chat.toolloop

>  Chat.toolloop (pr, max_steps=10, trace_func:Optional[<built-
>                     infunctioncallable>]=None, cont_func:Optional[<built-
>                     infunctioncallable>]=<function noop>, temp=None,
>                     maxtok=4096, maxthinktok=0, stream=False, prefill='',
>                     tool_choice:Optional[dict]=None)

*Add prompt `pr` to dialog and get a response from Claude, automatically
following up with `tool_use` messages*

<table>
<colgroup>
<col style="width: 6%" />
<col style="width: 25%" />
<col style="width: 34%" />
<col style="width: 34%" />
</colgroup>
<thead>
<tr>
<th></th>
<th><strong>Type</strong></th>
<th><strong>Default</strong></th>
<th><strong>Details</strong></th>
</tr>
</thead>
<tbody>
<tr>
<td>pr</td>
<td></td>
<td></td>
<td>Prompt to pass to Claude</td>
</tr>
<tr>
<td>max_steps</td>
<td>int</td>
<td>10</td>
<td>Maximum number of tool requests to loop through</td>
</tr>
<tr>
<td>trace_func</td>
<td>Optional</td>
<td>None</td>
<td>Function to trace tool use steps (e.g <code>print</code>)</td>
</tr>
<tr>
<td>cont_func</td>
<td>Optional</td>
<td>noop</td>
<td>Function that stops loop if returns False</td>
</tr>
<tr>
<td>temp</td>
<td>NoneType</td>
<td>None</td>
<td>Temperature</td>
</tr>
<tr>
<td>maxtok</td>
<td>int</td>
<td>4096</td>
<td>Maximum tokens</td>
</tr>
<tr>
<td>maxthinktok</td>
<td>int</td>
<td>0</td>
<td>Maximum thinking tokens</td>
</tr>
<tr>
<td>stream</td>
<td>bool</td>
<td>False</td>
<td>Stream response?</td>
</tr>
<tr>
<td>prefill</td>
<td>str</td>
<td></td>
<td>Optional prefill to pass to Claude as start of its response</td>
</tr>
<tr>
<td>tool_choice</td>
<td>Optional</td>
<td>None</td>
<td>Optionally force use of some tool</td>
</tr>
</tbody>
</table>

<details open class="code-fold">
<summary>Exported source</summary>

``` python
@patch
@delegates(Chat.__call__)
def toolloop(self:Chat,
             pr, # Prompt to pass to Claude
             max_steps=10, # Maximum number of tool requests to loop through
             trace_func:Optional[callable]=None, # Function to trace tool use steps (e.g `print`)
             cont_func:Optional[callable]=noop, # Function that stops loop if returns False
             **kwargs):
    "Add prompt `pr` to dialog and get a response from Claude, automatically following up with `tool_use` messages"
    n_msgs = len(self.h)
    r = self(pr, **kwargs)
    for i in range(max_steps):
        if r.stop_reason!='tool_use': break
        if trace_func: trace_func(self.h[n_msgs:]); n_msgs = len(self.h)
        r = self(**kwargs)
        if not (cont_func or noop)(self.h[-2]): break
    if trace_func: trace_func(self.h[n_msgs:])
    return r
```

</details>

We’ll start by re-running our previous request - we shouldn’t have to
manually pass back the `tool_use` message any more:

``` python
chat = Chat(model, tools=tools)
r = chat.toolloop('Can you tell me the email address for customer C1?')
r
```

    - Retrieving customer C1

The email address for customer C1 is john@example.com.

<details>

- id: `msg_01Fm2CY76dNeWief4kUW6r71`
- content:
  `[{'text': 'The email address for customer C1 is john@example.com.', 'type': 'text'}]`
- model: `claude-3-haiku-20240307`
- role: `assistant`
- stop_reason: `end_turn`
- stop_sequence: `None`
- type: `message`
- usage:
  `{'input_tokens': 720, 'output_tokens': 19, 'cache_creation_input_tokens': 0, 'cache_read_input_tokens': 0}`

</details>

Let’s see if it can handle the multi-stage process now – we’ll add
`trace_func=print` to see each stage of the process:

``` python
chat = Chat(model, tools=tools)
r = chat.toolloop('Please cancel all orders for customer C1 for me.', trace_func=print)
r
```

    - Retrieving customer C1
    [{'role': 'user', 'content': [{'type': 'text', 'text': 'Please cancel all orders for customer C1 for me.'}]}, {'role': 'assistant', 'content': [TextBlock(text="Okay, let's cancel all orders for customer C1:", type='text'), ToolUseBlock(id='toolu_01SvivKytaRHEdKixEY9dUDz', input={'customer_id': 'C1'}, name='get_customer_info', type='tool_use')]}, {'role': 'user', 'content': [{'type': 'tool_result', 'tool_use_id': 'toolu_01SvivKytaRHEdKixEY9dUDz', 'content': "{'name': 'John Doe', 'email': 'john@example.com', 'phone': '123-456-7890', 'orders': [{'id': 'O1', 'product': 'Widget A', 'quantity': 2, 'price': 19.99, 'status': 'Shipped'}, {'id': 'O2', 'product': 'Gadget B', 'quantity': 1, 'price': 49.99, 'status': 'Processing'}]}"}]}]
    - Cancelling order O1
    [{'role': 'assistant', 'content': [TextBlock(text="Based on the customer information, it looks like there are 2 orders for customer C1:\n- Order O1 for Widget A\n- Order O2 for Gadget B\n\nLet's cancel each of these orders:", type='text'), ToolUseBlock(id='toolu_01DoGVUPVBeDYERMePHDzUoT', input={'order_id': 'O1'}, name='cancel_order', type='tool_use')]}, {'role': 'user', 'content': [{'type': 'tool_result', 'tool_use_id': 'toolu_01DoGVUPVBeDYERMePHDzUoT', 'content': 'True'}]}]
    - Cancelling order O2
    [{'role': 'assistant', 'content': [ToolUseBlock(id='toolu_01XNwS35yY88Mvx4B3QqDeXX', input={'order_id': 'O2'}, name='cancel_order', type='tool_use')]}, {'role': 'user', 'content': [{'type': 'tool_result', 'tool_use_id': 'toolu_01XNwS35yY88Mvx4B3QqDeXX', 'content': 'True'}]}]
    [{'role': 'assistant', 'content': [TextBlock(text="I've successfully cancelled both orders O1 and O2 for customer C1. Please let me know if you need anything else!", type='text')]}]

I’ve successfully cancelled both orders O1 and O2 for customer C1.
Please let me know if you need anything else!

<details>

- id: `msg_01K1QpUZ8nrBVUHYTrH5QjSF`
- content:
  `[{'text': "I've successfully cancelled both orders O1 and O2 for customer C1. Please let me know if you need anything else!", 'type': 'text'}]`
- model: `claude-3-haiku-20240307`
- role: `assistant`
- stop_reason: `end_turn`
- stop_sequence: `None`
- type: `message`
- usage:
  `{'input_tokens': 921, 'output_tokens': 32, 'cache_creation_input_tokens': 0, 'cache_read_input_tokens': 0}`

</details>

OK Claude thinks the orders were cancelled – let’s check one:

``` python
chat.toolloop('What is the status of order O2?')
```

    - Retrieving order O2

The status of order O2 is now ‘Cancelled’ since I successfully cancelled
that order earlier.

<details>

- id: `msg_01XcXpFDwoZ3u1bFDf5mY8x1`
- content:
  `[{'text': "The status of order O2 is now 'Cancelled' since I successfully cancelled that order earlier.", 'type': 'text'}]`
- model: `claude-3-haiku-20240307`
- role: `assistant`
- stop_reason: `end_turn`
- stop_sequence: `None`
- type: `message`
- usage:
  `{'input_tokens': 1092, 'output_tokens': 26, 'cache_creation_input_tokens': 0, 'cache_read_input_tokens': 0}`

</details>

## Code interpreter

Here is an example of using `toolloop` to implement a simple code
interpreter with additional tools.

``` python
from toolslm.shell import get_shell
from fastcore.meta import delegates
import traceback
```

``` python
@delegates()
class CodeChat(Chat):
    imps = 'os, warnings, time, json, re, math, collections, itertools, functools, dateutil, datetime, string, types, copy, pprint, enum, numbers, decimal, fractions, random, operator, typing, dataclasses'
    def __init__(self, model: Optional[str] = None, ask:bool=True, **kwargs):
        super().__init__(model=model, **kwargs)
        self.ask = ask
        self.tools.append(self.run_cell)
        self.shell = get_shell()
        self.shell.run_cell('import '+self.imps)
```

We have one additional parameter to creating a `CodeChat` beyond what we
pass to [`Chat`](https://claudette.answer.ai/core.html#chat), which is
`ask` – if that’s `True`, we’ll prompt the user before running code.

``` python
@patch
def run_cell(
    self:CodeChat,
    code:str,   # Code to execute in persistent IPython session
): # Result of expression on last line (if exists); '#DECLINED#' if user declines request to execute
    "Asks user for permission, and if provided, executes python `code` using persistent IPython session."
    confirm = f'Press Enter to execute, or enter "n" to skip?\n```\n{code}\n```\n'
    if self.ask and input(confirm): return '#DECLINED#'
    try: res = self.shell.run_cell(code)
    except Exception as e: return traceback.format_exc()
    return res.stdout if res.result is None else res.result
```

We just pass along requests to run code to the shell’s implementation.
Claude often prints results instead of just using the last expression,
so we capture stdout in those cases.

``` python
sp = f'''You are a knowledgable assistant. Do not use tools unless needed.
Don't do complex calculations yourself -- use code for them.
The following modules are pre-imported for `run_cell` automatically:

{CodeChat.imps}

Never mention what tools you are using. Note that `run_cell` interpreter state is *persistent* across calls.

If a tool returns `#DECLINED#` report to the user that the attempt was declined and no further progress can be made.'''
```

``` python
def get_user(ignored:str='' # Unused parameter
            ): # Username of current user
    "Get the username of the user running this session"
    print("Looking up username")
    return 'Jeremy'
```

In order to test out multi-stage tool use, we create a mock function
that Claude can call to get the current username.

``` python
model = models[1]
```

``` python
chat = CodeChat(model, tools=[get_user], sp=sp, ask=True, temp=0.3)
```

Claude gets confused sometimes about how tools work, so we use examples
to remind it:

``` python
chat.h = [
    'Calculate the square root of `10332`', 'math.sqrt(10332)',
    '#DECLINED#', 'I am sorry but the request to execute that was declined and no further progress can be made.'
]
```

Providing a callable to toolloop’s `trace_func` lets us print out
information during the loop:

``` python
def _show_cts(h):
    for r in h:
        for o in r.get('content'):
            if hasattr(o,'text'): print(o.text)
            nm = getattr(o, 'name', None)
            if nm=='run_cell': print(o.input['code'])
            elif nm: print(f'{o.name}({o.input})')
```

…and toolloop’s `cont_func` callable let’s us provide a function which,
if it returns `False`, stops the loop:

``` python
def _cont_decline(c):
    return nested_idx(c, 'content', 'content') != '#DECLINED#'
```

Now we can try our code interpreter. We start by asking for a function
to be created, which we’ll use in the next prompt to test that the
interpreter is persistent.

``` python
pr = '''Create a 1-line function `checksum` for a string `s`,
that multiplies together the ascii values of each character in `s` using `reduce`.'''
chat.toolloop(pr, temp=0.2, trace_func=_show_cts, cont_func=_cont_decline)
```

    Press Enter to execute, or enter "n" to skip?
    ```
    checksum = lambda s: functools.reduce(lambda x, y: x * ord(y), s, 1)
    ```

    Create a 1-line function `checksum` for a string `s`,
    that multiplies together the ascii values of each character in `s` using `reduce`.
    Let me help you create that function using `reduce` and `functools`.
    checksum = lambda s: functools.reduce(lambda x, y: x * ord(y), s, 1)
    The function has been created. Let me explain how it works:
    1. It takes a string `s` as input
    2. Uses `functools.reduce` to multiply together all ASCII values
    3. `ord(y)` gets the ASCII value of each character
    4. The initial value is 1 (the third parameter to reduce)
    5. The lambda function multiplies the accumulator (x) with each new ASCII value

    You can test it with any string. For example, you could try `checksum("hello")` to see it in action.

The function has been created. Let me explain how it works: 1. It takes
a string `s` as input 2. Uses `functools.reduce` to multiply together
all ASCII values 3. `ord(y)` gets the ASCII value of each character 4.
The initial value is 1 (the third parameter to reduce) 5. The lambda
function multiplies the accumulator (x) with each new ASCII value

You can test it with any string. For example, you could try
`checksum("hello")` to see it in action.

<details>

- id: `msg_011pcGY9LbYqvRSfDPgCqUkT`
- content:
  `[{'text': 'The function has been created. Let me explain how it works:\n1. It takes a string`s`as input\n2. Uses`functools.reduce`to multiply together all ASCII values\n3.`ord(y)`gets the ASCII value of each character\n4. The initial value is 1 (the third parameter to reduce)\n5. The lambda function multiplies the accumulator (x) with each new ASCII value\n\nYou can test it with any string. For example, you could try`checksum(“hello”)`to see it in action.', 'type': 'text'}]`
- model: `claude-3-5-sonnet-20241022`
- role: `assistant`
- stop_reason: `end_turn`
- stop_sequence: `None`
- type: `message`
- usage:
  `{'input_tokens': 824, 'output_tokens': 125, 'cache_creation_input_tokens': 0, 'cache_read_input_tokens': 0}`

</details>

By asking for a calculation to be done on the username, we force it to
use multiple steps:

``` python
pr = 'Use it to get the checksum of the username of this session.'
chat.toolloop(pr, trace_func=_show_cts)
```

    Looking up username
    Use it to get the checksum of the username of this session.
    I'll first get the username using `get_user` and then apply our `checksum` function to it.
    get_user({'ignored': ''})
    Press Enter to execute, or enter "n" to skip?
    ```
    print(checksum("Jeremy"))
    ```

    Now I'll calculate the checksum of "Jeremy":
    print(checksum("Jeremy"))
    The checksum of the username "Jeremy" is 1134987783204. This was calculated by multiplying together the ASCII values of each character in "Jeremy".

The checksum of the username “Jeremy” is 1134987783204. This was
calculated by multiplying together the ASCII values of each character in
“Jeremy”.

<details>

- id: `msg_01UXvtcLzzykZpnQUT35v4uD`
- content:
  `[{'text': 'The checksum of the username "Jeremy" is 1134987783204. This was calculated by multiplying together the ASCII values of each character in "Jeremy".', 'type': 'text'}]`
- model: `claude-3-5-sonnet-20241022`
- role: `assistant`
- stop_reason: `end_turn`
- stop_sequence: `None`
- type: `message`
- usage:
  `{'input_tokens': 1143, 'output_tokens': 38, 'cache_creation_input_tokens': 0, 'cache_read_input_tokens': 0}`

</details>