/**
 * \file
 * \brief Some basic struct unit tests.
 */

#ifdef NDEBUG
#undef NDEBUG
#endif

#include "generated/structs/Test1.h"
#include "generated/structs/Test2.h"
#include "generated/structs/Test3.h"
#include "generated/structs/Test7.h"
#include <cassert>
#include <iostream>

static constexpr std::size_t len = 10;

template <std::endian endianness> void test1_encode_decode(void)
{
    using namespace A::B;

    C::Test1 src;
    src.field1 = 0x55;
    src.field2 = Enum1::C;
    src.field3 = 2.5f;

    C::Test1::Buffer buffer;
    assert(src.encode<endianness>(&buffer) == C::Test1::size);

    C::Test1 dst;
    assert(dst.decode<endianness>(&buffer) == C::Test1::size);
    assert(src == dst);

    /* Verify the values transferred. */
    assert(dst.field1 == 0x55);
    assert(dst.field2 == Enum1::C);
    assert(dst.field3 == 2.5f);

    std::array<std::byte, C::Test1::size * len> streambuf;
    using TestSpan = std::span<std::byte, C::Test1::size * len>;
    auto stream = byte_spanstream(TestSpan(streambuf));

    stream << dst;
    stream.seekg(0);

    C::Test1 from_stream;
    stream >> from_stream;

    /* Verify the values transferred. */
    assert(from_stream.field1 == 0x55);
    assert(from_stream.field2 == Enum1::C);
    assert(from_stream.field3 == 2.5f);

    for (std::size_t i = 0; i < len - 1; i++)
    {
        stream << from_stream;
    }
    assert(stream.good());

    stream << from_stream;
    assert(not stream.good());
}

template <std::endian endianness> void test2_encode_decode(void)
{
    using namespace A::B;

    Test2 src;
    src.field1 = 0x55;
    src.field2 = -500;
    src.field3 = 2.5f;

    Test2::Buffer buffer;
    assert(src.encode<endianness>(&buffer) == Test2::size);

    Test2 dst;
    assert(dst.decode<endianness>(&buffer) == Test2::size);
    assert(src == dst);

    /* Verify the values transferred. */
    assert(dst.field1 == 0x55);
    assert(dst.field2 == -500);
    assert(dst.field3 == 2.5f);
}

template <std::endian endianness> void test3_encode_decode(void)
{
    using namespace A::B;

    Test3 src = {};
    src.field1 = 70000;

    src.field2.field1 = 200;
    src.field2.field2 = Enum1::B;
    src.field2.field3 = -4000.0;

    src.field3.field1 = -100;
    src.field3.field2 = -300;
    src.field3.field3 = -5.0f;

    src.field4 = C::Enum2::green;

    Test3::Buffer buffer = {};
    assert(src.encode<endianness>(&buffer) == Test3::size);

    Test3 dst = {};
    assert(dst.decode<endianness>(&buffer) == Test3::size);
    assert(src == dst);

    assert(dst.field1 == 70000);

    assert(dst.field2.field1 == 200);
    assert(dst.field2.field2 == Enum1::B);
    assert(dst.field2.field3 == -4000.0);

    assert(dst.field3.field1 == -100);
    assert(dst.field3.field2 == -300);
    assert(dst.field3.field3 == -5.0f);

    assert(dst.field4 == C::Enum2::green);
}

void test7_toggle_bits()
{
    using namespace A::B;

    Test7 data;
    data.field1 = 0;

    data.toggle_field1_bit_field2();
    assert(data.field1 == 2);
    data.toggle_field1_bit_field2();
    assert(data.field1 == 0);

    data.toggle_field1_bit_field3();
    assert(data.field1 == 4);
    data.toggle_field1_bit_field3();
    assert(data.field1 == 0);
    assert(not data.get_field1_bit_field3());

    data.toggle_field1_bit_field4();
    assert(data.field1 == 8);
    data.toggle_field1_bit_field4();
    assert(data.field1 == 0);
    assert(not data.get_field1_bit_field4());

    data.toggle_field1_bit_field2();
    data.toggle_field1_bit_field3();
    data.toggle_field1_bit_field4();
    assert(data.field1 == 14);

    data.clear_field1_bit_field2();
    assert(data.field1 == 12);

    data.clear_field1_bit_field3();
    assert(data.field1 == 8);

    data.clear_field1_bit_field4();
    assert(data.field1 == 0);

    data.set_field1_bit_field2();
    data.set_field1_bit_field3();
    data.set_field1_bit_field4();
    assert(data.field1 == 14);

    assert(data.get_field1_bit_field3());
    assert(data.get_field1_bit_field4());

    data.set_field1_bit_field6(5);
    assert(data.get_field1_bit_field6() == 5);
    assert(data.field1 == ((5 << 8) + 14));
}

/**
 * A unit test for structs Test1.
 *
 * \return 0 on success.
 */
int main(void)
{
    test1_encode_decode<std::endian::native>();
    test1_encode_decode<std::endian::little>();
    test1_encode_decode<std::endian::big>();

    test2_encode_decode<std::endian::native>();
    test2_encode_decode<std::endian::little>();
    test2_encode_decode<std::endian::big>();

    test3_encode_decode<std::endian::native>();
    test3_encode_decode<std::endian::little>();
    test3_encode_decode<std::endian::big>();

    test7_toggle_bits();

    std::cout << "Success." << std::endl;
    return 0;
}
