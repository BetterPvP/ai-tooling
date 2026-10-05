# Step 3: Tests first

Write tests that fail now and pass when the slice is done. The user reviews these instead of the implementation, so
they must be short and readable.

1. Read the ACs in the issue. Write at least one test per `[auto]` AC, in the module the code will live in
   (`<module>/src/test/java/...`). JUnit 5 and Mockito are on the test classpath.
2. Name each test after its AC: `ac3_builderStopsWithoutWood()`. One behaviour per test.
3. Test behaviour through the public API the slice will add. Sketch the minimum production signatures needed to
   compile (empty methods or `throw new UnsupportedOperationException()`) and say so in the commit.
4. Run them: `./gradlew :<module>:test --tests '<TestClass>'`. They must compile and fail for the right reason.
5. Commit only the tests and the signatures: `test: AC1-AC4 for #<issue>`.
6. Tell the user which test covers which AC, and ask them to read the tests and reply `approve tests`.

Do not write the implementation in this step.
