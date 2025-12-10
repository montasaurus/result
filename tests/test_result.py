from __future__ import annotations

from typing import AsyncGenerator, Generator

import pytest

from result import (
    Err,
    Ok,
    OkErr,
    Result,
    UnwrapError,
    as_async_generator_result,
    as_async_result,
    as_generator_result,
    as_result,
)


def sq(i: int) -> Result[int, int]:
    return Ok(i * i)


async def sq_async(i: int) -> Result[int, int]:
    return Ok(i * i)


def to_err(i: int) -> Result[int, int]:
    return Err(i)


async def to_err_async(i: int) -> Result[int, int]:
    return Err(i)


# Lambda versions of the same functions, just for test/type coverage
def sq_lambda(i: int) -> Result[int, int]:
    return Ok(i * i)


def to_err_lambda(i: int) -> Result[int, int]:
    return Err(i)


def test_ok_factories() -> None:
    instance = Ok(1)
    assert instance._value == 1  # pyright: ignore[reportPrivateUsage]
    assert instance.is_ok() is True


def test_err_factories() -> None:
    instance = Err(2)
    assert instance._value == 2  # pyright: ignore[reportPrivateUsage]
    assert instance.is_err() is True


def test_eq() -> None:
    assert Ok(1) == Ok(1)
    assert Err(1) == Err(1)
    assert Ok(1) != Err(1)
    assert Ok(1) != Ok(2)
    assert Err(1) != Err(2)
    assert not (Ok(1) != Ok(1))
    assert Ok(1) != "abc"
    assert Ok("0") != Ok(0)


def test_hash() -> None:
    assert len({Ok(1), Err("2"), Ok(1), Err("2")}) == 2
    assert len({Ok(1), Ok(2)}) == 2
    assert len({Ok("a"), Err("a")}) == 2


def test_repr() -> None:
    """
    ``repr()`` returns valid code if the wrapped value's ``repr()`` does as well.
    """
    o = Ok(123)
    n = Err(-1)

    assert repr(o) == "Ok(123)"
    assert o == eval(repr(o))

    assert repr(n) == "Err(-1)"
    assert n == eval(repr(n))


def test_ok_value() -> None:
    res = Ok("haha")
    assert res.ok_value == "haha"


def test_err_value() -> None:
    res = Err("haha")
    assert res.err_value == "haha"


def test_ok() -> None:
    res = Ok("haha")
    assert res.is_ok() is True
    assert res.is_err() is False
    assert res.ok_value == "haha"


def test_err() -> None:
    res = Err(":(")
    assert res.is_ok() is False
    assert res.is_err() is True
    assert res.err_value == ":("


def test_err_value_is_exception() -> None:
    res = Err(ValueError("Some Error"))
    assert res.is_ok() is False
    assert res.is_err() is True

    with pytest.raises(UnwrapError):
        res.unwrap()

    try:
        res.unwrap()
    except UnwrapError as e:
        cause = e.__cause__
        assert isinstance(cause, ValueError)


def test_ok_method() -> None:
    o = Ok("yay")
    n = Err("nay")
    assert o.ok() == "yay"
    assert n.ok() is None  # type: ignore[func-returns-value]


def test_err_method() -> None:
    o = Ok("yay")
    n = Err("nay")
    assert o.err() is None  # type: ignore[func-returns-value]
    assert n.err() == "nay"


def test_expect() -> None:
    o = Ok("yay")
    n = Err("nay")
    assert o.expect("failure") == "yay"
    with pytest.raises(UnwrapError):
        n.expect("failure")


def test_expect_err() -> None:
    o = Ok("yay")
    n = Err("nay")
    assert n.expect_err("hello") == "nay"
    with pytest.raises(UnwrapError):
        o.expect_err("hello")


def test_unwrap() -> None:
    o = Ok("yay")
    n = Err("nay")
    assert o.unwrap() == "yay"
    with pytest.raises(UnwrapError):
        n.unwrap()


def test_unwrap_err() -> None:
    o = Ok("yay")
    n = Err("nay")
    assert n.unwrap_err() == "nay"
    with pytest.raises(UnwrapError):
        o.unwrap_err()


def test_unwrap_or() -> None:
    o = Ok("yay")
    n = Err("nay")
    assert o.unwrap_or("some_default") == "yay"
    assert n.unwrap_or("another_default") == "another_default"


def test_unwrap_or_else() -> None:
    o = Ok("yay")
    n = Err("nay")
    assert o.unwrap_or_else(str.upper) == "yay"
    assert n.unwrap_or_else(str.upper) == "NAY"


def test_unwrap_or_raise() -> None:
    o = Ok("yay")
    n = Err("nay")
    assert o.unwrap_or_raise(ValueError) == "yay"
    with pytest.raises(ValueError) as exc_info:
        n.unwrap_or_raise(ValueError)
    assert exc_info.value.args == ("nay",)


def test_map() -> None:
    o = Ok("yay")
    n = Err("nay")
    assert o.map(str.upper).ok() == "YAY"
    assert n.map(str.upper).err() == "nay"

    num = Ok(3)
    errnum = Err(2)
    assert num.map(str).ok() == "3"
    assert errnum.map(str).err() == 2


def test_map_or() -> None:
    o = Ok("yay")
    n = Err("nay")
    assert o.map_or("hay", str.upper) == "YAY"
    assert n.map_or("hay", str.upper) == "hay"

    num = Ok(3)
    errnum = Err(2)
    assert num.map_or("-1", str) == "3"
    assert errnum.map_or("-1", str) == "-1"


def test_map_or_else() -> None:
    o = Ok("yay")
    n = Err("nay")
    assert o.map_or_else(lambda: "hay", str.upper) == "YAY"
    assert n.map_or_else(lambda: "hay", str.upper) == "hay"

    num = Ok(3)
    errnum = Err(2)
    assert num.map_or_else(lambda: "-1", str) == "3"
    assert errnum.map_or_else(lambda: "-1", str) == "-1"


def test_map_err() -> None:
    o = Ok("yay")
    n = Err("nay")
    assert o.map_err(str.upper).ok() == "yay"
    assert n.map_err(str.upper).err() == "NAY"


def test_and_then() -> None:
    assert Ok(2).and_then(sq).and_then(sq).ok() == 16
    assert Ok(2).and_then(sq).and_then(to_err).err() == 4
    assert Ok(2).and_then(to_err).and_then(sq).err() == 2
    assert Err(3).and_then(sq).and_then(sq).err() == 3

    assert Ok(2).and_then(sq_lambda).and_then(sq_lambda).ok() == 16
    assert Ok(2).and_then(sq_lambda).and_then(to_err_lambda).err() == 4
    assert Ok(2).and_then(to_err_lambda).and_then(sq_lambda).err() == 2
    assert Err(3).and_then(sq_lambda).and_then(sq_lambda).err() == 3


def test_inspect() -> None:
    oks: list[int] = []

    def add_to_oks(x: int) -> None:
        return oks.append(x)

    assert Ok(2).inspect(add_to_oks) == Ok(2)
    assert Err("e").inspect(add_to_oks) == Err("e")
    assert oks == [2]


def test_inspect_err() -> None:
    errs: list[str] = []

    def add_to_errs(x: str) -> None:
        return errs.append(x)

    assert Ok(2).inspect_err(add_to_errs) == Ok(2)
    assert Err("e").inspect_err(add_to_errs) == Err("e")
    assert errs == ["e"]


def test_inspect_regular_fn() -> None:
    oks: list[str] = []

    def _add_to_oks(x: str) -> str:
        oks.append(x)
        return x + x

    assert Ok("hello").inspect(_add_to_oks) == Ok("hello")
    assert Err("error").inspect(_add_to_oks) == Err("error")
    assert oks == ["hello"]


@pytest.mark.asyncio
async def test_and_then_async() -> None:
    assert (
        await (await Ok(2).and_then_async(sq_async)).and_then_async(sq_async)
    ).ok() == 16
    assert (
        await (await Ok(2).and_then_async(sq_async)).and_then_async(to_err_async)
    ).err() == 4
    assert (
        await (await Ok(2).and_then_async(to_err_async)).and_then_async(to_err_async)
    ).err() == 2
    assert (
        await (await Err(3).and_then_async(sq_async)).and_then_async(sq_async)
    ).err() == 3


@pytest.mark.asyncio
async def test_map_async() -> None:
    async def str_upper_async(s: str) -> str:
        return s.upper()

    async def str_async(x: int) -> str:
        return str(x)

    o = Ok("yay")
    n = Err("nay")
    assert (await o.map_async(str_upper_async)).ok() == "YAY"
    assert (await n.map_async(str_upper_async)).err() == "nay"

    num = Ok(3)
    errnum = Err(2)
    assert (await num.map_async(str_async)).ok() == "3"
    assert (await errnum.map_async(str_async)).err() == 2


def test_or_else() -> None:
    assert Ok(2).or_else(sq).or_else(sq).ok() == 2
    assert Ok(2).or_else(to_err).or_else(sq).ok() == 2
    assert Err(3).or_else(sq).or_else(to_err).ok() == 9
    assert Err(3).or_else(to_err).or_else(to_err).err() == 3

    assert Ok(2).or_else(sq_lambda).or_else(sq).ok() == 2
    assert Ok(2).or_else(to_err_lambda).or_else(sq_lambda).ok() == 2
    assert Err(3).or_else(sq_lambda).or_else(to_err_lambda).ok() == 9
    assert Err(3).or_else(to_err_lambda).or_else(to_err_lambda).err() == 3


def test_isinstance_result_type() -> None:
    o = Ok("yay")
    n = Err("nay")
    assert isinstance(o, OkErr)
    assert isinstance(n, OkErr)
    assert not isinstance(1, OkErr)


def test_error_context() -> None:
    n = Err("nay")
    with pytest.raises(UnwrapError) as exc_info:
        n.unwrap()
    exc = exc_info.value
    assert exc.result is n


def test_slots() -> None:
    """
    Ok and Err have slots, so assigning arbitrary attributes fails.
    """
    o = Ok("yay")
    n = Err("nay")
    with pytest.raises(AttributeError):
        o.some_arbitrary_attribute = 1  # type: ignore[attr-defined]
    with pytest.raises(AttributeError):
        n.some_arbitrary_attribute = 1  # type: ignore[attr-defined]


def test_as_result() -> None:
    """
    ``as_result()`` turns functions into ones that return a ``Result``.
    """

    @as_result(ValueError)
    def good(value: int) -> int:
        return value

    @as_result(IndexError, ValueError)
    def bad(value: int) -> int:
        raise ValueError

    good_result = good(123)
    bad_result = bad(123)

    assert isinstance(good_result, Ok)
    assert good_result.unwrap() == 123
    assert isinstance(bad_result, Err)
    assert isinstance(bad_result.unwrap_err(), ValueError)


def test_as_result_other_exception() -> None:
    """
    ``as_result()`` only catches the specified exceptions.
    """

    @as_result(ValueError)
    def f() -> int:
        raise IndexError

    with pytest.raises(IndexError):
        f()


def test_as_result_unwraps() -> None:
    @as_result(ValueError)
    def raises_unwrapping_error(value: int) -> int:
        Err(IndexError("Test Error")).unwrap()
        return value

    @as_result(IndexError, ValueError)
    def does_not_raise_unwrapping_error(value: int) -> int:
        Err(IndexError("Test Error")).unwrap()
        return value

    with pytest.raises(UnwrapError):
        raises_unwrapping_error(123)

    err_response = does_not_raise_unwrapping_error(123)
    assert isinstance(err_response.unwrap_err(), IndexError)


def test_as_result_invalid_usage() -> None:
    """
    Invalid use of ``as_result()`` raises reasonable errors.
    """
    message = "requires one or more exception types"

    with pytest.raises(TypeError, match=message):

        @as_result()  # No exception types specified
        def f() -> int:  # pyright: ignore[reportUnusedFunction]
            return 1

    with pytest.raises(TypeError, match=message):

        @as_result("not an exception type")  # type: ignore[arg-type]
        def g() -> int:  # pyright: ignore[reportUnusedFunction]
            return 1


def test_as_result_type_checking() -> None:
    """
    The ``as_result()`` is a signature-preserving decorator.
    """

    @as_result(ValueError)
    def f(a: int) -> int:
        return a

    res: Result[int, ValueError]
    res = f(123)  # No mypy error here.
    assert res.ok() == 123


@pytest.mark.asyncio
async def test_as_async_result() -> None:
    """
    ``as_async_result()`` turns functions into ones that return a ``Result``.
    """

    @as_async_result(ValueError)
    async def good(value: int) -> int:
        return value

    @as_async_result(IndexError, ValueError)
    async def bad(value: int) -> int:
        raise ValueError

    good_result = await good(123)
    bad_result = await bad(123)

    assert isinstance(good_result, Ok)
    assert good_result.unwrap() == 123
    assert isinstance(bad_result, Err)
    assert isinstance(bad_result.unwrap_err(), ValueError)


@pytest.mark.asyncio
async def test_as_async_result_unwraps() -> None:
    @as_async_result(ValueError)
    async def raises_unwrapping_error(value: int) -> int:
        Err(IndexError("Test Error")).unwrap()
        return value

    @as_async_result(IndexError, ValueError)
    async def does_not_raise_unwrapping_error(value: int) -> int:
        Err(IndexError("Test Error")).unwrap()
        return value

    with pytest.raises(UnwrapError):
        await raises_unwrapping_error(123)

    err_response = await does_not_raise_unwrapping_error(123)
    assert isinstance(err_response.unwrap_err(), IndexError)


def test_as_generator_result_ok() -> None:
    @as_generator_result(ValueError)
    def my_generator(val: int) -> Generator[int, None, None]:
        yield val
        yield val + 1
        yield val + 2

    result = my_generator(1)
    assert next(result) == Ok(1)
    assert next(result) == Ok(2)
    assert next(result) == Ok(3)
    with pytest.raises(StopIteration):
        next(result)


def test_as_generator_result_err() -> None:
    @as_generator_result(ValueError)
    def my_generator(val: int) -> Generator[int, None, None]:
        yield val
        raise ValueError("Test Error")

    result = my_generator(1)
    assert next(result) == Ok(1)
    error_result = next(result)
    assert isinstance(error_result, Err)
    assert error_result.err_value.args[0] == "Test Error"
    with pytest.raises(StopIteration):
        next(result)


def test_as_generator_result_unwraps() -> None:
    @as_generator_result(ValueError)
    def raises_unwrapping_error(value: int) -> Generator[int, None, None]:
        Err(IndexError("Test Error")).unwrap()
        yield 5

    @as_generator_result(IndexError, ValueError)
    def does_not_raise_unwrapping_error(value: int) -> Generator[int, None, None]:
        yield 3
        Err(IndexError("Test Error")).unwrap()
        yield 5

    raising_generator = raises_unwrapping_error(123)
    with pytest.raises(UnwrapError):
        next(raising_generator)

    running_generator = does_not_raise_unwrapping_error(123)
    assert next(running_generator) == Ok(3)
    assert next(running_generator).unwrap_err().args[0] == "Test Error"
    with pytest.raises(StopIteration):
        next(running_generator)


def test_as_generator_result_with_send() -> None:
    @as_generator_result(ValueError)
    def my_generator() -> Generator[int, int, None]:
        val = yield 1
        val = yield val if val is not None else 0  # pyright: ignore[reportUnnecessaryComparison]
        val = yield val + 2 if val is not None else 0  # pyright: ignore[reportUnnecessaryComparison]

    result = my_generator()
    assert next(result) == Ok(1)
    assert result.send(10) == Ok(10)
    assert result.send(20) == Ok(22)
    with pytest.raises(StopIteration):
        next(result)


def test_as_generator_result_with_send_and_exception() -> None:
    @as_generator_result(ValueError)
    def my_generator() -> Generator[Result[int, ValueError], int, None]:
        val: int | None = yield Ok(1)
        try:
            if val is not None:  # pyright: ignore[reportUnnecessaryComparison]
                raise ValueError("Send Value Error")
        except ValueError as e:
            val = yield Err(e)

        val = yield Ok(val) if val is not None else Ok(0)  # pyright: ignore[reportUnnecessaryComparison]
        val = yield Ok(val + 2) if val is not None else Ok(0)  # pyright: ignore[reportUnnecessaryComparison]

    result = my_generator()
    assert next(result) == Ok(Ok(1))

    error_result = result.send(10)
    assert error_result.unwrap().unwrap_err().args[0] == "Send Value Error"

    assert result.send(20) == Ok(Ok(20))
    assert result.send(30) == Ok(Ok(32))
    with pytest.raises(StopIteration):
        next(result)


@pytest.mark.asyncio
async def test_as_async_generator_result_ok() -> None:
    @as_async_generator_result(ValueError)
    async def my_generator(val: int) -> AsyncGenerator[int, None]:
        yield val
        yield val + 1
        yield val + 2

    result = my_generator(1)
    assert await anext(result) == Ok(1)
    assert await anext(result) == Ok(2)
    assert await anext(result) == Ok(3)
    with pytest.raises(StopAsyncIteration):
        await anext(result)


@pytest.mark.asyncio
async def test_as_async_generator_result_err() -> None:
    @as_async_generator_result(ValueError)
    async def my_generator(val: int) -> AsyncGenerator[int, None]:
        yield val
        raise ValueError("Test Error")

    result = my_generator(1)
    assert await anext(result) == Ok(1)
    error_result = await anext(result)
    assert isinstance(error_result, Err)
    assert error_result.err_value.args[0] == "Test Error"

    with pytest.raises(StopAsyncIteration):
        await anext(result)


@pytest.mark.asyncio
async def test_as_async_generator_result_unwraps() -> None:
    @as_async_generator_result(ValueError)
    async def raises_unwrapping_error(value: int) -> AsyncGenerator[int, None]:
        Err(IndexError("Test Error")).unwrap()
        yield 5

    @as_async_generator_result(IndexError, ValueError)
    async def does_not_raise_unwrapping_error(value: int) -> AsyncGenerator[int, None]:
        yield 3
        Err(IndexError("Test Error")).unwrap()
        yield 5

    raising_generator = raises_unwrapping_error(123)
    with pytest.raises(UnwrapError):
        await anext(raising_generator)

    running_generator = does_not_raise_unwrapping_error(123)
    assert await anext(running_generator) == Ok(3)
    assert (await anext(running_generator)).unwrap_err().args[0] == "Test Error"
    with pytest.raises(StopAsyncIteration):
        await anext(running_generator)


@pytest.mark.asyncio
async def test_as_async_generator_result_with_send() -> None:
    @as_async_generator_result(ValueError)
    async def my_generator() -> AsyncGenerator[int, int]:
        val = yield 1
        val = yield val if val is not None else 0  # pyright: ignore[reportUnnecessaryComparison]
        val = yield val + 2 if val is not None else 0  # pyright: ignore[reportUnnecessaryComparison]

    result = my_generator()
    assert await anext(result) == Ok(1)
    assert await result.asend(10) == Ok(10)
    assert await result.asend(20) == Ok(22)
    with pytest.raises(StopAsyncIteration):
        await anext(result)


@pytest.mark.asyncio
async def test_as_async_generator_result_with_send_and_exception() -> None:
    @as_async_generator_result(ValueError)
    async def my_generator() -> AsyncGenerator[Result[int, ValueError], int]:
        val: int | None = yield Ok(1)
        try:
            if val is not None:  # pyright: ignore[reportUnnecessaryComparison]
                raise ValueError("Async Send Value Error")
        except ValueError as e:
            val = yield Err(e)

        val = yield Ok(val) if val is not None else Ok(0)  # pyright: ignore[reportUnnecessaryComparison]
        val = yield Ok(val + 2) if val is not None else Ok(0)  # pyright: ignore[reportUnnecessaryComparison]

    result = my_generator()
    assert await anext(result) == Ok(Ok(1))

    # This now correctly gets the Err directly
    error_result = await result.asend(10)
    assert error_result.unwrap().unwrap_err().args[0] == "Async Send Value Error"

    # Correctly resumes with the sent value after the exception
    assert await result.asend(20) == Ok(Ok(20))
    assert await result.asend(30) == Ok(Ok(32))
    with pytest.raises(StopAsyncIteration):
        await anext(result)
